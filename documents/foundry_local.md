# Microsoft Foundry Local Nedir?

Foundry Local, büyük dil modellerini tamamen kullanıcının kendi
cihazında, buluta bağlanmadan çalıştırmayı sağlayan uçtan uca bir
yerel yapay zekâ çözümüdür. Optimize edilmiş bir model kataloğu, hafif
bir çalışma zamanı (runtime) ve bir SDK sunar.

## Öne çıkan özellikler

- Model indirme ve yönetimini otomatik olarak yapar.
- CPU/NPU hızlandırmasını kullanarak çıkarım (inference) yapar.
- OpenAI uyumlu bir REST API sunar; bu sayede mevcut `openai` istemci
  kütüphaneleri sadece `base_url` değiştirilerek kullanılabilir.
- Sohbet tamamlama (chat completions), embedding üretimi ve ses
  transkripsiyonu (Whisper tabanlı) destekler.

## Bu projede nasıl kullanılıyor?

`src/local_rag/providers.py` dosyasındaki `FoundryLocalRuntime` sınıfı,
Foundry Local'in embedding istemcisini soru-cevap bölümlerini
vektörleştirmek için, OpenAI uyumlu sohbet uç noktasını ise nihai
cevabı üretmek için kullanır. Bu sayede uygulamanın geri kalanı
Foundry Local'in iç detaylarını bilmek zorunda kalmaz.
