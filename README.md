# Ardinal — kurulum (uçtan uca)

Bu dosya: **indir → kur → cüzdan → ETH → swap/stake → mining başlat**. Başka bir şey okuman şart değil.

**Risk:** Gerçek ETH harcanır; stake ve swap geri alınamayabilir. Küçük miktarla dene.

---

## 0) Lazım olanlar

- Mac, Linux veya **Ubuntu sunucu**
- İnternet
- [OpenRouter](https://openrouter.ai/) hesabı + **API key** (otomatik mining için)
- Biraz **Base ağı ETH** (gas + gerekirse stake)

**Güvenlik:** API anahtarı ve cüzdan kelimelerini **kimseyle paylaşma**, ekran görüntüsü atma. `.env` dosyanı GitHub’a yükleme.

---

## 1) Projeyi indir

**Git varsa** (repo adresini kendi linkinle değiştir):

```bash
git clone https://github.com/zacnider/ardinal.git
cd ardinal
```

**Git yoksa:** GitHub’da **Code → Download ZIP** → Zip’i aç → **Terminal** aç → o klasöre gir:

```bash
cd ~/Downloads/ardinal-main
```

`ls` yaz; listede **`ardi`** ve **`setup-local.sh`** görünüyorsa doğru klasördesin. Görünmüyorsa bir üst klasöre çık (`cd ..`) ve tekrar dene.

**Terminal nerede:** Mac’te ⌘+Boşluk → “Terminal” yaz → Enter.

---

## 2) Bilgisayara araçları kur (Mac veya Linux masaüstü)

### 2.1 Node.js

[https://nodejs.org/](https://nodejs.org/) adresinden **LTS** indir, kur. Kurulumdan sonra Terminal’i **kapatıp yeniden aç**.

Kontrol:

```bash
node -v
python3 --version
```

İkisi de bir sürüm yazıyorsa devam. `node` yok diyorsa Node’u kurup Terminal’i yenile.

### 2.2 Proje kurulumu

**Hâlâ ardinal klasöründeyken:**

```bash
chmod +x ardi setup-local.sh
bash setup-local.sh
```

Bu komut internetten dosya indirir; birkaç dakika sürebilir. Hata yoksa bitti.

---

## 3) Ubuntu sunucuda kurulum (isteğe bağlı)

Sunucuda proje klasöründesin; **sudo veya root** yetkin olsun:

```bash
chmod +x install-server.sh ardi setup-local.sh
bash install-server.sh
```

Mac’te **bu scripti çalıştırma** (Ubuntu/Debian içindir).

---

## 4) Cüzdan

### 4.1 İlk kez: genelde hazır gelir

`bash setup-local.sh` (veya `install-server.sh`) sonunda cüzdan **otomatik** oluşturulur. Ekstra bir şey yapmana gerek yok.

### 4.2 Adresini ve durumu gör

Proje klasöründe:

```bash
./ardi status
```

veya

```bash
./ardi preflight
```

Çıktıda **`0x` ile başlayan adres** senin ajan cüzdanın. Bunu not al; ETH buraya, `.env` içindeki `ARDI_STAKER` da buna yazılacak.

### 4.3 Kelime öbeği (mnemonic) veya private key — sadece yedek için

**Sadece kendi bilgisayarında**, güvenli bir ortamda:

```bash
bash export-wallet-secrets.sh
```

Çıkan kelimeleri **kağıda veya şifre kasasına** yaz; **asla** sohbet, mail, GitHub’a koyma. Bu kelimeler cüzdanının tam anahtarıdır.

---

## 5) ETH gönder

1. `./ardi status` ile adresini al.  
2. Borsa veya cüzdanından **Base** ağını seç.  
3. Bu adrese **ETH** gönder (hem işlem ücreti hem stake için yeterli miktarda; tam rakam `gas` ve `buy-and-stake --quote` ile anlaşılır).

Kontrol:

```bash
./ardi gas
```

---

## 6) Stake (oyuna uygun olmak)

Sırayla; her komuttan sonra çıkan yazıyı oku.

```bash
./ardi preflight
```

Eksik stake / gas diyorsa:

```bash
./ardi stake
```

ETH ile tek seferde **swap + stake** yolu (önce plan, para gitmez):

```bash
./ardi buy-and-stake --quote
```

Çıktıyı oku. Onaylıyorsan (kilit gününü quote’a göre seç):

```bash
./ardi buy-and-stake --yes --lock-days 3
```

`3` yerine kendi seçtiğin gün sayısını yaz (zorunlu).

Son kontrol:

```bash
./ardi preflight
```

Burada oyun için yol **açık** görünüyorsa mining’e geçebilirsin.

---

## 7) Mining’i başlat (OpenRouter)

### 7.1 API key

[openrouter.ai](https://openrouter.ai/) → hesap → API keys → yeni anahtar oluştur.

### 7.2 `.env` dosyası

Proje klasöründe:

```bash
cp env.example .env
nano .env
```

(`nano` yerine istediğin metin editörünü kullanabilirsin.)

Şunları doldur:

- `OPENROUTER_API_KEY` = OpenRouter anahtarın  
- `OPENROUTER_MODEL` = kullanacağın modelin **tam adı** (OpenRouter model sayfasındaki id, ör. `anthropic/claude-3.5-sonnet`)  
- `ARDI_STAKER` = `./ardi status` ile gördüğün **aynı** `0x...` adres (**mutlaka** doldur)

Kaydet. `nano` için: Ctrl+O, Enter, Ctrl+X.

### 7.3 Çalıştır

```bash
python3 openrouter_mine.py --auto-chain
```

- **Durdurmak:** Ctrl+C  
- **Aynı cüzdanı** iki bilgisayarda **aynı anda** çalıştırma (hata ve nonce çakışması).

**SSL / sertifika hatası** olursa önce:

```bash
pip3 install --user certifi
```

Hâlâ olmazsa (son çare, daha az güvenli):

```bash
python3 openrouter_mine.py --auto-chain --insecure-ssl
```

### 7.4 Sunucuda pencere kapanmasın diye (isteğe bağlı)

```bash
sudo apt install -y tmux
tmux new -s ardi
cd /path/to/ardinal
python3 openrouter_mine.py --auto-chain
```

Ayrılmak: **Ctrl+b** sonra **d**. Geri: `tmux attach -t ardi`

---

## 8) Komut özeti (kopyalalık)

| Adım | Komut |
|------|--------|
| İndir | `git clone ...` veya ZIP aç → `cd ardinal` |
| Mac/Linux kur | `chmod +x ardi setup-local.sh` → `bash setup-local.sh` |
| Ubuntu kur | `bash install-server.sh` |
| Adres / kontrol | `./ardi status` veya `./ardi preflight` |
| ETH kontrol | `./ardi gas` |
| Stake menüsü | `./ardi stake` |
| Swap+stake planı | `./ardi buy-and-stake --quote` |
| Swap+stake uygula | `./ardi buy-and-stake --yes --lock-days GÜN` |
| Mining | `cp env.example .env` → düzenle → `python3 openrouter_mine.py --auto-chain` |

---

## 9) Takıldığın yerde

| Belirti | Ne yap |
|---------|--------|
| `setup-local.sh` yok | Yanlış klasördesin; `ls` ile `ardi` gör. |
| `node: command not found` | Node LTS kur, Terminal’i yeniden aç. |
| `OPENROUTER_API_KEY` hatası | `.env` proje kökünde mi, satır başında boşluk yok mu. |
| Commit yanlış / staker | `.env` içinde `ARDI_STAKER` = `./ardi status` adresi. |

## 10) Yeni cüzdana geçiş için en temiz akış:

   

1) Çalışan miner/process’i durdur

openrouter_mine.py, ./ardi loop vb. açıksa kapat.

2) Eski cüzdanı yedekle (silme)
Proje kökünde:
```bash
cd /Users/nihataltuntas/Desktop/projeler/ardinal
mv run-home/.openclaw-wallet "run-home/.openclaw-wallet.bak-$(date +%Y%m%d-%H%M%S)"
```
3) Yeni cüzdan oluştur
   ```bash
export HOME="$PWD/run-home"
export AWP_WALLET_BIN="$PWD/awp-wallet/scripts/wallet-cli.js"
node "$AWP_WALLET_BIN" init
```
5) Yeni adresi doğrula
 ```bash
./ardi status
```
6) .env’i yeni adrese güncelle
   
ARDI_STAKER= satırını ./ardi status’daki yeni 0x... adres yap.
7) Yeni Cüzdanın Private Key ve Seed'ini al
 ```bash
bash export-wallet-secrets.sh
```

8) Yeni cüzdana ETH gönder (Base)
Sonra kontrol:
 ```bash
./ardi gas
```
9) Stake ve eligibility
     ```bash
./ardi preflight
./ardi stake
./ardi buy-and-stake --quote
./ardi buy-and-stake --yes --lock-days 3
./ardi preflight
```
10) Mining başlat
 ```bash
python3 openrouter_mine.py --auto-chain
```
