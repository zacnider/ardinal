#!/usr/bin/env python3
"""
Tek tur: ./ardi context → OpenRouter ile cevap listesi → sırayla ./ardi commit (paralel yok).

Gerekli ortam:
  Proje kökünde .env (OPENROUTER_API_KEY=...) otomatik okunur; yoksa export kullan.
  export OPENROUTER_API_KEY="sk-or-..."
  export OPENROUTER_MODEL="anthropic/claude-sonnet-4"   # veya openrouter.ai/models listesinden

Zorunlu (gerçek commit için; --dry-run hariç):
  .env veya export: ARDI_STAKER="0x..."  # ./ardi status ile aynı ajan adresi

İsteğe bağlı:
  export ARDI_ROOT="/path/to/ardinal"   # varsayılan: bu scriptin bulunduğu klasör

Kullanım:
  cd .../ardinal && python3 openrouter_mine.py
  python3 openrouter_mine.py --dry-run
  python3 openrouter_mine.py --max-commits 3

Sürekli (tek süreç — paralel çalıştırma):
  python3 openrouter_mine.py --watch
  export OPENROUTER_POLL_SEC=25   # --watch döngüsü arası (varsayılan 25; dar pencere için 10–15)

Commit sonrası reveal + inscribe (./ardi loop ile aynı anda çalıştırma):
  python3 openrouter_mine.py --watch --auto-chain
  # --auto-chain tek başına da sürekli döngüdür (--watch otomatik; tek tur: --once)

Commit penceresi yokken bekle-yenile (varsayılan 20s; Ctrl+C ile dur):
  OPENROUTER_NO_EPOCH_SLEEP_SEC=20
  OPENROUTER_NO_EPOCH_MAX_TRIES=0   # 0 = sınırsız tekrar

VRF sonrası inscribe tekrar (auto-chain):
  OPENROUTER_VRF_RETRY_SEC=20
  OPENROUTER_VRF_INSCRIBE_MAX_TRIES=60

TLS (macOS python.org: sertifika hatası):
  pip3 install certifi
  veya macOS’ta: /Applications/Python\\ 3.11/Install Certificates.command
  Geçici (güvensiz): export OPENROUTER_SSL_INSECURE=1  veya  --insecure-ssl
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[misc, assignment]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_dotenv_optional(project_dir: Path) -> None:
    """ARDI_ROOT'tan bağımsız: script dizinindeki .env — mevcut os.environ değerlerini ezmez."""
    path = project_dir / ".env"
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ[key] = val


def root() -> Path:
    r = os.environ.get("ARDI_ROOT")
    if r:
        return Path(r).resolve()
    return Path(__file__).resolve().parent


def run_ardi(args: list[str]) -> subprocess.CompletedProcess[str]:
    ardi = root() / "ardi"
    if not ardi.is_file():
        sys.stderr.write(f"Missing {ardi} — run from ardinal project root.\n")
        sys.exit(1)
    return subprocess.run(
        [str(ardi), *args],
        cwd=str(root()),
        capture_output=True,
        text=True,
        check=False,
    )


def make_ssl_context(*, insecure: bool) -> ssl.SSLContext:
    if insecure:
        sys.stderr.write(
            "WARNING: TLS certificate verification is OFF "
            "(--insecure-ssl or OPENROUTER_SSL_INSECURE=1).\n"
        )
        return ssl._create_unverified_context()
    ctx = ssl.create_default_context()
    try:
        import certifi

        ctx.load_verify_locations(certifi.where())
    except ImportError:
        pass
    return ctx


def parse_context_json(stdout: str) -> dict:
    s = stdout.strip()
    if not s.startswith("{"):
        i = s.find('{"status"')
        if i >= 0:
            s = s[i:]
    dec = json.JSONDecoder()
    obj, _ = dec.raw_decode(s)
    return obj


def openrouter_chat(
    api_key: str, model: str, user_prompt: str, *, ssl_ctx: ssl.SSLContext
) -> str:
    body = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You solve short dictionary riddles for an on-chain game. "
                        "Each answer must be ONE word or lemma in the riddle's `language` "
                        "(en, ko, zh, ja, de, fr, ...). No explanations. "
                        "Return ONLY a JSON array, no markdown fences, like: "
                        '[{"word_id":123,"answer":"word"},...]'
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/awp-worknet/ardi-skill",
            "X-Title": "ardinal-openrouter-mine",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl_ctx) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP {e.code}: {err}") from e
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected OpenRouter response: {payload!r}") from e


def extract_json_array(text: str):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    a = text.find("[")
    b = text.rfind("]")
    if a >= 0 and b > a:
        return json.loads(text[a : b + 1])
    raise ValueError(f"Could not parse JSON array from model: {text[:500]}...")


def fetch_commits_doc() -> dict:
    p = run_ardi(["commits"])
    if p.returncode != 0:
        raise RuntimeError(p.stderr or p.stdout or "commits failed")
    return parse_context_json(p.stdout or "")


def pending_row(doc: dict, epoch: int, word_id: int) -> dict | None:
    for row in (doc.get("data") or {}).get("pending") or []:
        if row.get("epoch_id") == epoch and row.get("word_id") == word_id:
            return row
    return None


def reveal_ready(row: dict) -> bool:
    if row.get("status") != "committed":
        return False
    if row.get("reveal_tx"):
        return False
    sec = row.get("next_reveal_in_seconds")
    if sec is None:
        return True
    try:
        return int(sec) <= 0
    except (TypeError, ValueError):
        return True


def auto_reveal_inscribe(epoch: int, word_ids: list[int]) -> None:
    """Poll ./ardi commits; reveal when ready; then try inscribe (losers will error)."""
    if not word_ids:
        return
    sys.stderr.write(
        f"[auto-chain] epoch={epoch} words={word_ids} — reveal bekleniyor (poll 15s, max ~30dk)\n"
    )
    pending_reveal = set(word_ids)
    for _ in range(120):
        try:
            doc = fetch_commits_doc()
        except (RuntimeError, json.JSONDecodeError) as e:
            sys.stderr.write(f"[auto-chain] commits parse: {e}\n")
            time.sleep(15)
            continue
        done = set()
        for wid in pending_reveal:
            row = pending_row(doc, epoch, wid)
            if not row:
                sys.stderr.write(f"[auto-chain] word {wid} deftere yok, atlanıyor\n")
                done.add(wid)
                continue
            if row.get("status") == "lost":
                done.add(wid)
                continue
            if row.get("reveal_tx"):
                done.add(wid)
                continue
            if reveal_ready(row):
                sys.stderr.write(f"[auto-chain] reveal epoch={epoch} word={wid}\n")
                rp = run_ardi(
                    ["reveal", "--epoch", str(epoch), "--word-id", str(wid)]
                )
                sys.stdout.write(rp.stdout or "")
                sys.stderr.write(rp.stderr or "")
                if rp.returncode == 0:
                    done.add(wid)
                else:
                    sys.stderr.write(
                        f"[auto-chain] reveal hata rc={rp.returncode} — 30s sonra tekrar\n"
                    )
                time.sleep(3)
        pending_reveal -= done
        if not pending_reveal:
            break
        time.sleep(15)
    else:
        sys.stderr.write("[auto-chain] reveal zaman aşımı; kalanları elle ./ardi reveal\n")

    sys.stderr.write("[auto-chain] VRF için ~45s bekleniyor, sonra inscribe denemesi\n")
    time.sleep(45)

    vrf_retry_sec = max(
        5, int(os.environ.get("OPENROUTER_VRF_RETRY_SEC", "20") or "20")
    )
    vrf_max = max(1, int(os.environ.get("OPENROUTER_VRF_INSCRIBE_MAX_TRIES", "60") or "60"))

    def inscribe_vrf_still_pending(doc: dict) -> bool:
        na = (doc.get("_internal") or {}).get("next_action") or ""
        if na == "wait_vrf":
            return True
        d = doc.get("data") or {}
        if str(d.get("vrf_state", "")).lower() == "pending":
            return True
        msg = (doc.get("message") or "").lower()
        return "vrf pending" in msg or "draw in flight" in msg

    for wid in word_ids:
        for attempt in range(1, vrf_max + 1):
            sys.stderr.write(
                f"[auto-chain] inscribe epoch={epoch} word={wid} "
                f"(deneme {attempt}/{vrf_max})\n"
            )
            ip = run_ardi(["inscribe", "--epoch", str(epoch), "--word-id", str(wid)])
            sys.stdout.write(ip.stdout or "")
            sys.stderr.write(ip.stderr or "")
            if ip.returncode != 0:
                sys.stderr.write(
                    f"[auto-chain] inscribe rc={ip.returncode}, bu kelime için durduruldu\n"
                )
                break
            try:
                idoc = parse_context_json(ip.stdout or "{}")
            except json.JSONDecodeError:
                time.sleep(vrf_retry_sec)
                continue
            if inscribe_vrf_still_pending(idoc):
                sys.stderr.write(
                    f"[auto-chain] VRF hâlâ pending — {vrf_retry_sec}s sonra tekrar inscribe\n"
                )
                time.sleep(vrf_retry_sec)
                continue
            break
        time.sleep(2)


def run_commit_cycle(
    *,
    max_commits: int,
    dry_run: bool,
    ssl_ctx: ssl.SSLContext,
    api_key: str,
    model: str,
    staker: str,
    skip_epoch_id: int | None,
) -> tuple[str, int | None, list[int]]:
    """
    Tek tur: context → OpenRouter → commit.
    Dönüş: (sonuç, epochId, bu turda commit atılan word_id listesi).
    """
    eid_none: int | None = None
    sleep_sec = max(5, int(os.environ.get("OPENROUTER_NO_EPOCH_SLEEP_SEC", "20")))
    max_tries_raw = os.environ.get("OPENROUTER_NO_EPOCH_MAX_TRIES", "0").strip()
    max_tries = int(max_tries_raw) if max_tries_raw else 0  # 0 = sınırsız

    doc: dict | None = None
    attempt = 0
    while True:
        ctx = run_ardi(["context"])
        if ctx.returncode != 0:
            sys.stderr.write(ctx.stderr or ctx.stdout or "context failed\n")
            return "context_fail", eid_none, []

        try:
            doc = parse_context_json(ctx.stdout or "")
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Bad JSON from context:\n{ctx.stdout}\n{e}\n")
            return "context_fail", eid_none, []

        data = doc.get("data") or {}
        riddles = data.get("riddles") or []
        if riddles:
            break

        epoch_id = data.get("epochId")
        eid = epoch_id if isinstance(epoch_id, int) else None
        msg = doc.get("message", "No riddles / no commit window.")
        attempt += 1
        if max_tries > 0 and attempt >= max_tries:
            print(msg, file=sys.stderr)
            return "no_window", eid, []

        sys.stderr.write(
            f"[context] {msg}\n"
            f"[context] {sleep_sec}s bekleniyor, tekrar denenecek "
            f"(deneme {attempt}"
            + (f"/{max_tries})…\n" if max_tries > 0 else ")… Ctrl+C durdur\n")
        )
        time.sleep(sleep_sec)

    assert doc is not None
    data = doc.get("data") or {}
    riddles = data.get("riddles") or []
    epoch_id = data.get("epochId")
    eid = epoch_id if isinstance(epoch_id, int) else None

    if skip_epoch_id is not None and eid is not None and eid == skip_epoch_id:
        print(
            f"[watch] epoch {epoch_id} already committed this session — skip\n",
            file=sys.stderr,
        )
        return "skip_epoch", eid, []

    max_c = max(1, min(max_commits, 5))
    user = json.dumps(
        {
            "epochId": epoch_id,
            "message": doc.get("message"),
            "riddles": riddles,
            "instruction": (
                f"Return a JSON array with at most {max_c} objects. "
                "Only include riddles you are reasonably confident about. "
                'Each object: {{"word_id": <int>, "answer": "<single word/lemma>"}}. '
                "Answer language MUST match each riddle's `language` field."
            ),
        },
        ensure_ascii=False,
        indent=2,
    )

    print("Calling OpenRouter…", file=sys.stderr)
    try:
        raw = openrouter_chat(api_key, model, user, ssl_ctx=ssl_ctx)
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e).upper() or "SSL" in str(e).upper():
            sys.stderr.write(
                "\nSSL hatası. Dene:\n"
                "  pip3 install certifi\n"
                "veya (macOS python.org) Applications içindeki "
                "\"Install Certificates.command\"\n"
                "veya geçici: --insecure-ssl\n\n"
            )
        raise

    pairs = extract_json_array(raw)
    if not isinstance(pairs, list):
        raise ValueError("Model did not return a JSON array")

    valid_ids = {int(r["wordId"]) for r in riddles if "wordId" in r}
    commits: list[tuple[int, str]] = []
    for item in pairs:
        if len(commits) >= max_c:
            break
        wid = int(item["word_id"])
        ans = str(item["answer"]).strip().strip('"').split()[0]
        if wid not in valid_ids:
            print(f"Skip unknown word_id {wid}", file=sys.stderr)
            continue
        if not ans:
            continue
        commits.append((wid, ans))

    print(json.dumps(commits, ensure_ascii=False, indent=2))
    if dry_run:
        return "dry_run", eid, [w for w, _ in commits]

    if not commits:
        print("[watch] model returned no commits", file=sys.stderr)
        return "empty_model", eid, []

    committed_wids: list[int] = []
    for wid, ans in commits:
        print(f"\ncommit word_id={wid} answer={ans!r}", file=sys.stderr)
        cp = run_ardi(
            [
                "commit",
                "--word-id",
                str(wid),
                "--answer",
                ans,
                "--staker",
                staker,
            ]
        )
        sys.stdout.write(cp.stdout or "")
        sys.stderr.write(cp.stderr or "")
        if cp.returncode != 0:
            sys.stderr.write(f"\ncommit failed rc={cp.returncode}\n")
            return "context_fail", eid, committed_wids
        committed_wids.append(wid)

    if committed_wids:
        print(
            "\nCommitted. Sonra: ./ardi commits → reveal → inscribe "
            "(veya --auto-chain veya ./ardi loop).\n",
            file=sys.stderr,
        )
        return "committed", eid, committed_wids
    return "empty_model", eid, []


def acquire_watch_lock():
    if fcntl is None:
        sys.stderr.write("--watch requires Unix (fcntl).\n")
        sys.exit(1)
    lock_path = root() / ".openrouter_mine.lock"
    fp = open(lock_path, "w")
    try:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.stderr.write(
            "Başka bir openrouter_mine --watch zaten çalışıyor. İkinci kopya açma.\n"
        )
        sys.exit(1)
    return fp


def main() -> None:
    load_dotenv_optional(Path(__file__).resolve().parent)

    ap = argparse.ArgumentParser(description="Ardi: context → OpenRouter → commits")
    ap.add_argument("--max-commits", type=int, default=5, help="Max commits this run (epoch cap is 5)")
    ap.add_argument("--dry-run", action="store_true", help="Only print model JSON, no commits")
    ap.add_argument(
        "--insecure-ssl",
        action="store_true",
        help="Disable TLS verify (only if cert chain broken; prefer: pip3 install certifi)",
    )
    ap.add_argument(
        "--watch",
        action="store_true",
        help="Tek süreçte bekle: commit penceresi açılınca bir tur çalıştır; epoch başına en fazla bir batch.",
    )
    ap.add_argument(
        "--poll-sec",
        type=int,
        default=None,
        help="--watch için bekleme saniye (varsayılan: OPENROUTER_POLL_SEC veya 25)",
    )
    ap.add_argument(
        "--auto-chain",
        action="store_true",
        help="Commit sonrası ./ardi commits ile bekle → reveal → inscribe (./ardi loop ile aynı anda çalıştırma)",
    )
    ap.add_argument(
        "--once",
        action="store_true",
        help="Tek tur (context→commit; --auto-chain varsa o epoch için reveal/inscribe) sonra çık — sürekli değil",
    )
    args = ap.parse_args()

    if args.auto_chain and not args.once and not args.watch:
        args.watch = True
        sys.stderr.write(
            "[openrouter] --auto-chain sürekli epoch için --watch otomatik açıldı "
            "(tek tur: --auto-chain --once).\n"
        )
    if args.watch and args.dry_run:
        sys.stderr.write(
            "Uyarı: --watch + --dry-run her turda OpenRouter çağırır; kısa test için kullan.\n"
        )

    insecure_ssl = args.insecure_ssl or os.environ.get(
        "OPENROUTER_SSL_INSECURE", ""
    ).strip().lower() in ("1", "true", "yes")
    ssl_ctx = make_ssl_context(insecure=insecure_ssl)

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    model = os.environ.get("OPENROUTER_MODEL", "").strip() or "anthropic/claude-3.5-sonnet"
    staker = os.environ.get("ARDI_STAKER", "").strip()

    if not api_key:
        sys.stderr.write("Set OPENROUTER_API_KEY in the environment.\n")
        sys.exit(1)
    if not args.dry_run and not staker:
        sys.stderr.write(
            "ARDI_STAKER yok. .env dosyasına kendi cüzdan adresini yaz (./ardi status çıktısındaki 0x...):\n"
            "  ARDI_STAKER=0x...\n"
            "Sadece model çıktısı denemek için: python3 openrouter_mine.py --dry-run\n"
        )
        sys.exit(1)

    poll = args.poll_sec
    if poll is None:
        poll = int(os.environ.get("OPENROUTER_POLL_SEC", "25") or "25")
    poll = max(10, poll)

    if args.watch:
        lock_fp = acquire_watch_lock()
        last_done: int | None = None
        sys.stderr.write(
            f"[watch] poll={poll}s Ctrl+C ile dur."
            + (" --auto-chain açık (reveal/inscribe bu süreçte).\n" if args.auto_chain else " Reveal/inscribe: --auto-chain veya ./ardi loop.\n")
        )
        try:
            while True:
                out, eid, wids = run_commit_cycle(
                    max_commits=args.max_commits,
                    dry_run=args.dry_run,
                    ssl_ctx=ssl_ctx,
                    api_key=api_key,
                    model=model,
                    staker=staker,
                    skip_epoch_id=last_done,
                )
                if out == "committed" and eid is not None:
                    last_done = eid
                    if args.auto_chain and wids and not args.dry_run:
                        try:
                            auto_reveal_inscribe(eid, wids)
                        except (RuntimeError, OSError, ValueError) as ex:
                            sys.stderr.write(f"[auto-chain] {ex}\n")
                elif out in ("context_fail",):
                    sys.stderr.write("[watch] hata — 60s sonra tekrar.\n")
                    time.sleep(60)
                    continue
                if args.once:
                    break
                time.sleep(poll)
        except KeyboardInterrupt:
            sys.stderr.write("\n[watch] durduruldu.\n")
        finally:
            try:
                fcntl.flock(lock_fp.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            lock_fp.close()
        return

    out, eid, wids = run_commit_cycle(
        max_commits=args.max_commits,
        dry_run=args.dry_run,
        ssl_ctx=ssl_ctx,
        api_key=api_key,
        model=model,
        staker=staker,
        skip_epoch_id=None,
    )
    if out == "no_window":
        sys.exit(2)
    if out == "context_fail":
        sys.exit(1)
    if out == "empty_model" and not args.dry_run:
        sys.exit(3)
    if args.auto_chain and out == "committed" and eid is not None and wids and not args.dry_run:
        try:
            auto_reveal_inscribe(eid, wids)
        except (RuntimeError, OSError, ValueError) as ex:
            sys.stderr.write(f"[auto-chain] {ex}\n")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError) as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(1)
