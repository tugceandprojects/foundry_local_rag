# Projeyi Anlama ve Sunma Rehberi

## 1. Projenin çözdüğü problem

Genel amaçlı bir dil modeli, kuruma veya kullanıcıya ait özel belgeleri bilmez.
Tüm belgeyi her soruda modele vermek de bağlam sınırı, hız ve doğruluk sorunları
oluşturur. Bu proje, yalnızca soruyla ilgili belge bölümlerini bulur ve modele
verir. Böylece cevap özel verilere dayanır, kaynak gösterir ve cihazdan dışarı
veri çıkarmaz.

## 2. Bir soru sorulduğunda ne olur?

1. Soru Foundry Local embedding modeliyle sayısal vektöre çevrilir.
2. SQLite'taki her belge bölümünün vektörüyle kosinüs benzerliği hesaplanır.
3. En yüksek puanlı `top_k` bölüm seçilir.
4. Puanlar güven eşiğinin altındaysa sistem cevap vermeyi reddeder.
5. Seçilen bölümler, kaynak etiketleriyle sistem prompt'una eklenir.
6. Yerel sohbet modeli yalnızca bu bağlamdan cevap üretir.
7. Arayüz cevapla birlikte getirilen kaynakları ve puanları gösterir.

## 3. Kodun katmanları

`loaders.py`, `.txt`, `.md` ve `.pdf` dosyalarından sayfa sayfa metin çıkarır.
PDF'lerde her sayfa ayrı bir birim olarak ele alınır ki sonradan "sayfa 7"
gibi doğru bir kaynak gösterilebilsin.

`chunking.py`, bir sayfanın/dosyanın metnini aramaya uygun parçalara ayırır.
Overlap kullanılması, parça sınırında kalan anlamın tamamen kaybolmasını önler.

`database.py`, SQL ayrıntılarını uygulamanın geri kalanından saklar. Veritabanı
tek bir dosyadır ve ayrı bir sunucu gerektirmez.

`providers.py`, Microsoft Foundry Local SDK'sını küçük bir arayüze dönüştürür.
Model adı veya SDK çağrıları değişirse esas olarak bu dosya güncellenir.

`retrieval.py`, yapay zekâ üretiminden farklı olarak deterministik arama
katmanıdır. Aynı vektörler için aynı sıralamayı verir.

`service.py`, retrieval ve generation adımlarını birleştirir. Burada prompt
kuralları ve yetersiz bilgi davranışı bulunur.

`cli.py` ile `app.py`, aynı iş mantığının iki farklı kullanıcı arayüzüdür.

## 4. Neden bu şekilde tasarlandı?

Tek bir `main.py` başlangıç için kolaydır fakat test, bakım ve anlatım zorlaşır.
Katmanlı tasarımda her sınıfın tek sorumluluğu vardır. Foundry SDK'sını sahte
nesnelerle değiştirebildiğimiz için model indirmeden test çalıştırabiliriz.
Bu yaklaşım dependency inversion ve separation of concerns ilkelerini gösterir.

## 5. Öğrenmen gereken konular

Öncelik sırasıyla:

1. Python temelleri: fonksiyon, sınıf, dataclass, type hint, context manager.
2. Sanal ortam ve paket yönetimi: `venv`, `pip`, `pyproject.toml`.
3. Git: commit, branch, `.gitignore`, anlamlı commit mesajları.
4. SQL ve SQLite: tablo, primary key, index, transaction, SELECT/INSERT.
5. RAG: retrieve, augment, generate; hallucination ve grounding.
6. Embedding: vektör, boyut, semantik yakınlık, kosinüs benzerliği.
7. Prompt tasarımı: sistem mesajı, bağlam sınırı, kaynaklandırma, fallback.
8. Test: unit test, fake/stub, arrange-act-assert, edge case.
9. Yazılım mimarisi: katmanlar, sorumluluk ayrımı, dependency injection.
10. Değerlendirme: retrieval doğruluğu, cevap doğruluğu, gecikme ve bellek.

## 6. Sunumda canlı gösterim

Önce belgelerde cevabı olan bir soru sorun. Kaynak bölümünü ve benzerlik
puanını gösterin. Ardından belgelerde hiç bulunmayan bir soru sorun ve sistemin
uydurmak yerine “Bu bilgi belgelerde bulunamadı.” dediğini gösterin. Son olarak
internet bağlantısını kapatıp aynı soruyu tekrar sorarak yerel çalışmayı kanıtlayın.

## 7. Savunmada gelebilecek sorular

**Neden SQLite?** Küçük yerel veri kümesinde sunucusuz, taşınabilir ve anlaşılır
olduğu için. Büyük ölçekte özel vektör veritabanı seçerdim.

**Neden kosinüs benzerliği?** Vektörlerin büyüklüğünden çok yönlerini, yani
semantik yakınlığı karşılaştırmak için.

**Model neden doğrudan cevaplamıyor?** Özel belgeleri eğitim verisinde
bulunmayabilir. Retrieval ile cevap kanıta dayandırılır.

**Halüsinasyonu tamamen engeller mi?** Hayır. Eşik, sınırlayıcı prompt ve kaynak
gösterimi riski azaltır; ayrıca sistematik değerlendirme gerekir.

**Neden iki model var?** Embedding modeli arama için vektör üretir; sohbet modeli
doğal dil cevabı üretir. Görevleri ve optimizasyonları farklıdır.

**PDF'lerde sayfa numarası nasıl korunuyor?** `loaders.py`, PDF'i tek bir metin
yerine sayfa listesi olarak okur. `ingestion.py` her sayfayı ayrı ayrı
parçalayıp veritabanına sayfa numarasıyla kaydeder. Böylece "sayfa 7'de..."
gibi kaynak gösterimi mümkün olur; düz `.txt`/`.md` dosyalarında sayfa kavramı
olmadığı için "bölüm N" etiketi kullanılır.

**Taranmış (resim) bir PDF yüklersem ne olur?** `pypdf`'in `extract_text()`
metodu, sayfada gerçek bir metin katmanı yoksa (örn. sayfa fotoğrafının
taranmasıyla oluşmuş PDF) boş döner ve o sayfa atlanır. OCR bu projenin
kapsamı dışındadır; geliştirme fikri olarak sunulabilir.

## 8. Dört haftalık kişisel çalışma planı

### 1. hafta

Python, sanal ortam, Git ve Foundry Local kurulumunu öğren. `providers.py`
içindeki model yükleme akışını elle çalıştır.

### 2. hafta

Chunking, embedding, kosinüs benzerliği ve SQLite bölümlerini öğren.
Veritabanını SQLite Viewer eklentisiyle incele.

### 3. hafta

Ingestion ve retrieval akışını debugger ile satır satır izle. Farklı `top_k`,
`chunk_size` ve `min_score` değerlerini deneyip sonuçları kaydet.

### 4. hafta

Test senaryolarını genişlet, kendi belgelerini ekle, README'yi kişiselleştir,
performans ölçümü yap ve demo sunumunu prova et.

