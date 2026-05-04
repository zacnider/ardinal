# Ardinal — sıfırdan başlayanlar için kurulum rehberi (Türkçe)

Amaç: bilgisayarında veya bir **Ubuntu sunucuda** projeyi ayağa kaldırıp **Ardi** oyununda commit atmaya kadar gitmek.

Daha teknik veya sunucu odaklı detay için: **`SETUP.md`**.

**Bu dosyaları sen yazmıyorsun:** `setup-local.sh`, `ardi` vb. hazır bir **şablon GitHub reposundan** veya **zip** ile gelir; sonra tek komutla kurulum yaparsın. Repoyu kim açacak, repoda ne olur/olmaz: **`PUBLIC-REPO.md`**.

---

## 1) Bu proje ne işe yarıyor?

- **Ardi (Ardinals):** Base ağında kelime bulmacası tarzı bir oyun. Belirli aralıklarla sorular gelir, cevap verirsin, zincire **commit** atarsın.
- Bu klasördeki araçlar:
  - **`./ardi`** → Cüzdan ve zincir işlemleri (preflight, commit, stake, vb.).
  - **`openrouter_mine.py`** → Yapay zekâ (OpenRouter üzerinden bir dil modeli) ile cevap üretip otomatik commit denemesi (isteğe bağlı).

**Önemli:** Gerçek para (ETH) ve stake riski vardır. Küçük miktarla başla, anlamadığın adımı atlama.

---

## 2) Önce hazırlaman gerekenler

| Ne | Neden |
|----|--------|
| **Bir bilgisayar** | Mac veya Linux (Ubuntu) uygun. Windows’ta en kolayı: **WSL2** veya doğrudan **Ubuntu sunucu**. |
| **İnternet** | Kurulum ve oyun zincir üzerinden. |
| **Şablon repoyu klonlamak veya zip indirmek** | İçinde `ardi`, `setup-local.sh`, `openrouter_mine.py` olsun (bunları elle oluşturma; dağıtan kişi repoya koyar). |
| **[OpenRouter](https://openrouter.ai/) hesabı + API anahtarı** | Otomatik mining (`openrouter_mine.py`) kullanacaksan. |
| **Biraz Base ağı ETH** | İşlem ücreti (gas) ve gerekiyorsa **stake / buy-and-stake** için. |

**Güvenlik (kısa):**

- **API anahtarı** ve **cüzdan yedeği** (kelimeler) kimseyle paylaşılmaz, ekran görüntüsü atılmaz.
- `.env` ve `run-home/` **GitHub’a yüklenmez** (repoda `.gitignore` ile engellenir).

### Projeyi ilk kez almak (git)

Aşağıdaki adresi, **senin veya ekibinin yayınladığı** public repo ile değiştir:

```bash
git clone https://github.com/KULLANICI/ardinal-starter.git
cd ardinal-starter
```

Git kullanmak istemezsen: GitHub’da **Code → Download ZIP** (yine public şablon repodan); zip’i açıp terminalde o klasöre `cd` ile gir.

Sonraki adımlar (Mac veya Linux): bu rehberdeki **`bash setup-local.sh`** veya Ubuntu sunucuda **`bash install-server.sh`**.

---

## 3) “Terminal” nedir, nereden açılır?

Komutları **tek tek yazıp Enter’a basacağın** siyah veya renkli metin penceresi.

- **Mac:** `Spotlight` (⌘ + Boşluk) → **Terminal** yaz → Enter.
- **Ubuntu:** Uygulamalar → **Terminal**.

Sonra proje klasörüne girmen gerekir. Örnek (yol seninkiyle aynı olmayabilir):

```bash
cd ~/Desktop/projeler/ardinal
```

`cd` = “change directory” = şu klasöre gir. `ls` yazarsan klasördeki dosyaları listeler.

Bundan sonra bu rehberdeki komutların çoğunu **ardinal klasörünün içindeyken** çalıştıracağız.

---

## 4) Mac’te kurulum — sade anlatım

Burada anlattığımız şey şu: bilgisayarına **birkaç hazır program** (Node, Python zaten var mı bakıyoruz), sonra proje klasöründe **tek bir kurulum komutu** çalıştırıyorsun. Kod yazmıyorsun; kopyalayıp terminale yapıştırıyorsun.

### Adım 1 — Projeyi bilgisayara al

Önce **ardinal** diye bir klasörün olsun (içinde `ardi`, `setup-local.sh` dosyaları görünecek). Bunu ya **GitHub’dan klonlayarak** ya da **zip indirip açarak** yaptın; detay yukarıda “Projeyi ilk kez almak” bölümünde.

Klasörü **İndirilenler**’e de, **Masaüstü**’ne de koyabilirsin; önemli olan Terminal’de o klasöre girebilmek.

### Adım 2 — Terminal’i aç, proje klasörüne gir

**⌘ + Boşluk** tuşlarına bas, **Terminal** yaz, Enter.

Açılan pencerede şunu yazıp Enter’a bas (yolu kendi klasörüne göre değiştir; Finder’da klasöre sağ tıklayıp yol kopyalanabiliyorsa oradan alabilirsin):

```bash
cd ~/Desktop/projeler/ardinal
```

Burada `cd` = “şu klasöre gir” demek. Yanlış yerdeysen Finder’da ardinal klasörünün üstüne tıkla, yolu bir yerden not al, `cd` satırını ona göre düzelt.

İçeriği görmek için:

```bash
ls
```

Listede `ardi` ve `setup-local.sh` görünüyorsa doğru yerdesin.

### Adım 3 — Node.js var mı bak

Aracın içindeki cüzdan kısmı **Node** diye bir ortam istiyor. Terminalde şunu yaz:

```bash
node -v
```

**v18** veya üstü (tercihen **v20**) gibi bir şey çıkıyorsa tamam, bir sonraki adıma geç.

**“command not found”** veya çok eski bir sürüm çıkıyorsa: tarayıcıdan [nodejs.org](https://nodejs.org/) aç, **LTS** sürümünü indir, çift tıklayıp kurulum sihirbazını bitir. Kurulumdan sonra **Terminal penceresini kapatıp yeni bir Terminal aç**, tekrar `node -v` yaz — bu sefer bir sürüm numarası görmelisin.

### Adım 4 — Python var mı bak

Aynı Terminalde:

```bash
python3 --version
```

Bir sürüm yazıyorsa (ör. 3.10, 3.12) genelde yeter. Hiç yoksa [python.org](https://www.python.org/downloads/) üzerinden macOS için indirip kurabilirsin veya (ileri seviye) Homebrew ile kurulur; çoğu Mac’te zaten vardır.

### Adım 5 — Asıl kurulum (bir kez)

Hâlâ **ardinal klasörünün içindeyken** şu iki satırı sırayla yapıştır, her birinden sonra Enter:

```bash
chmod +x ardi setup-local.sh
bash setup-local.sh
```

İkinci komut **internetten dosya indirir**, bir süre bekletir; hata yazmazsa iş bitmiş demektir. Bu adım senin için **cüzdan altyapısını** ve **zincir aracını** bu klasörün içine kurar; ev dizinine dağıtmaz.

### Adım 6 — İlk kontrol

```bash
./ardi preflight
```

Burada bir JSON veya mesaj görürsün; “bir şeyler eksik” diyorsa metni oku (çoğunlukla ETH veya stake ile ilgilidir). Sonraki bölümlerde gas ve stake anlatılıyor.

### Adım 7 — Mining sırasında “sertifika” hatası çıkarsa (sadece gerekirse)

Bazı Mac’lerde Python, OpenRouter’a bağlanırken güvenlik sertifikasında takılır. O zaman:

```bash
pip3 install --user certifi
```

Hâlâ olmazsa `openrouter_mine.py` için dokümanda geçen `--insecure-ssl` son çaredir; önce `certifi` yeter.

**Mac özeti:** Klasörü al → Terminal → `cd` ile içine gir → Node ve Python tamam mı bak → `chmod` + `bash setup-local.sh` → `./ardi preflight`. Hepsi bu.

---

## 5) Yol B — Ubuntu sunucu (önerilen: VPS)

Sunucuya SSH ile bağlandıktan sonra, **ardinal klasörünün olduğu dizine** git.

**Tek komutla** sistem paketleri + Node + proje kurulumu (root veya `sudo` yetkisi gerekir):

```bash
cd ~/ardinal
chmod +x install-server.sh ardi setup-local.sh
bash install-server.sh
```

Bu script **sadece Ubuntu/Debian tarzı** sistemlerde çalışır (`apt`). Mac’te kullanma.

---

## 6) Cüzdan: ilk kez

Kurulum bittiyinde cüzdan genelde oluşturulmuş olur. Kontrol:

```bash
./ardi status
```

veya

```bash
./ardi preflight
```

Çıktıda bir **Ethereum adresi** (`0x` ile başlar) görürsün. Bu adres **senin ajan cüzdanın**.

- **Yeni cüzdan:** Bu adrese **Base ağında ETH** gönder (borsadan veya cüzdanından “Base” ağını seçerek).
- **Yeni adres istiyorum / eskiyi sildim:** Detay için `SETUP.md` veya daha önceki “cüzdan sıfırlama” notların; kısaca: `run-home/.openclaw-wallet` yedeğini al, sil/taşı, sonra `HOME=.../run-home` ile `node awp-wallet/scripts/wallet-cli.js init` (ileri seviye).

---

## 7) Zincir hazırlığı (sıra önemli)

Hepsini **ardinal klasöründe**, `./ardi` ile yaparsın.

### 7.1 Genel kontrol

```bash
./ardi preflight
```

Çıktıyı oku. “OK” veya yeşil / tamam mesajına yakınsa bir sonraki adıma geç.

### 7.2 Gas (ETH yeterli mi?)

```bash
./ardi gas
```

ETH azsa, **Base** üzerinde bu adrese gönder.

### 7.3 Stake (oyuna girebilmek için)

```bash
./ardi stake
```

Burada farklı yollar anlatılır. ETH ile otomatik yol için genelde:

**Önce sadece fiyat / plan (zincirde işlem yok):**

```bash
./ardi buy-and-stake --quote
```

Çıktıyı oku. Onaylıyorsan (kilit günü dahil):

```bash
./ardi buy-and-stake --yes --lock-days 3
```

`3` yerine quote’ta konuştuğun **gün sayısını** yazman gerekir; rakam yanlışsa işlem beklentinle olmayabilir.

Sonra tekrar:

```bash
./ardi preflight
```

Stake tamamsa mining veya manuel commit aşamasına geçilir.

---

## 8) Otomatik mining için `.env` dosyası

Ardinal klasöründe **`.env`** oluştur. Repoda `env.example` varsa:

```bash
cp env.example .env
nano .env
```

Yoksa `nano .env` ile sıfırdan aç. Örnek içerik (kendi anahtarınla doldur):

```env
OPENROUTER_API_KEY=sk-or-v3-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
ARDI_STAKER=0xSeninCüzdanAdresinBuraya
```

- **`OPENROUTER_API_KEY`:** OpenRouter sitesinden oluşturduğun anahtar.
- **`OPENROUTER_MODEL`:** OpenRouter’da seçtiğin modelin **tam id**’si (sitede model sayfasında yazar).
- **`ARDI_STAKER`:** `./ardi status` ile gördüğün adres ile **aynı** olsun; yoksa commit yanlış staker’a gidebilir.

Dosyayı kaydet, çık (`nano` için: Ctrl+O Enter, Ctrl+X).

---

## 9) Mining’i başlat

Yine ardinal klasöründe:

```bash
python3 openrouter_mine.py --auto-chain
```

- Bu komut **uzun süre çalışır**; durdurmak için **Ctrl+C**.
- **Aynı cüzdanı** iki bilgisayarda aynı anda çalıştırma (nonce çakışması).

**Sunucuda sürekli açık kalsın** istiyorsan `tmux` kullan:

```bash
sudo apt install -y tmux
tmux new -s ardi
cd ~/ardinal
python3 openrouter_mine.py --auto-chain
```

Ayrılmak için: **Ctrl+b** bırak, sonra **d** (küçük harf). Geri girmek: `tmux attach -t ardi`

İçerideyken ayrılmak için ayrıca şunu da yazabilirsin: `tmux detach`

---

## 10) Manuel denemek istersen (AI olmadan)

```bash
./ardi context
```

Gelen bulmacalara kendin karar verip:

```bash
./ardi commit --word-id SAYI --answer "tek_kelime" --staker 0xSeninAdresin
```

Epoch ve kurallar için resmi dokümantasyon: repoda veya `ardi-skill/SKILL.md` (ayrı klonlanabilir).

---

## 11) Sık takılan yerler

| Sorun | Ne yap |
|--------|--------|
| `setup-local.sh: No such file` | Yanlış klasördesin veya dosya kopyalanmamış. `ls` ile kontrol et. |
| `ardi-agent yok` | `bash setup-local.sh` veya `bash install-server.sh` (Ubuntu) çalıştır. |
| OpenRouter SSL hatası | `pip3 install --user certifi` veya `openrouter_mine.py --insecure-ssl` (son çare). |
| `OPENROUTER_API_KEY` yok | `.env` dosyası proje kökünde mi, satır doğru mu. |
| Commit başarısız / stake | `./ardi preflight` ve `./ardi stake` çıktısına göre ilerle. |
| İki yerde aynı anda mining | Birini durdur; aynı cüzdan için tek süreç. |

---

## 12) Sonraki okumalar

- **`SETUP.md`** — Uzak sunucu, rsync, `install-server.sh`, sık hatalar.
- **`ardi-skill/SKILL.md`** — Oyun ve komutların resmi açıklaması (GitHub’dan klonlanır).

Bu rehber “en az bilgiyle en güvenli sıra” içindir; risk ve gas maliyeti her zaman sende.
