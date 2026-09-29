# RAG (Retrieval-Augmented Generation) Nedir?

RAG, bir dil modelinin cevabını kendi eğitim verisi yerine dışarıdan
sağlanan belgelere dayandırmasını sağlayan bir tasarım desenidir. Üç
adımdan oluşur:

1. **Retrieve (Getir):** Kullanıcının sorusuyla anlamca en yakın belge
   bölümleri bulunur.
2. **Augment (Zenginleştir):** Bulunan bölümler, modele gönderilecek
   prompt'a bağlam olarak eklenir.
3. **Generate (Üret):** Model, yalnızca bu bağlamı kullanarak cevap üretir.

## RAG neden kullanılır?

Genel amaçlı bir dil modeli, kuruma veya kullanıcıya özel belgeleri
bilmez. Bu bilgiyi modele öğretmenin iki yolu vardır: modeli yeniden
eğitmek (pahalı ve yavaş) veya soruyla ilgili metni her seferinde
bağlam olarak vermek (RAG). RAG, doğru bilgiye dayanan, kaynak
gösterebilen ve daha az "uydurma" (hallucination) içeren cevaplar
üretir.

## Sınırlamaları

RAG, halüsinasyonu tamamen ortadan kaldırmaz. Getirilen bölümler
alakasızsa veya güven eşiğinin altındaysa sistemin cevap vermeyi
reddetmesi (fallback) önemlidir. Bu projede bu davranış `RagService`
sınıfında uygulanır.
