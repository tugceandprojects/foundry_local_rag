# Sıkça Sorulan Sorular

## Verilerim internete çıkar mı?

Hayır. Belgeler yalnızca yerel SQLite veritabanında saklanır ve
embedding/sohbet çıkarımı Foundry Local üzerinden cihazda çalışır.
İnternet yalnızca ilk model indirmesi için gereklidir.

## Hangi dosya türleri desteklenir?

Şu an için yalnızca UTF-8 kodlamalı `.txt` ve `.md` dosyaları
desteklenir. PDF ve DOCX desteği ileride eklenebilir.

## Sistem her soruya cevap verir mi?

Hayır. Getirilen belge bölümlerinin benzerlik puanı, ayarlanabilir bir
güven eşiğinin (`RAG_MIN_SCORE`) altındaysa sistem "Bu bilgi
belgelerde bulunamadı." der ve dil modelini hiç çağırmaz. Bu, uydurma
cevap riskini azaltır.

## Neden SQLite kullanılıyor?

Küçük, yerel veri kümeleri için SQLite sunucusuz, taşınabilir ve tek
dosyadan oluşan basit bir çözümdür. Büyük ölçekli kullanımda özel bir
vektör veritabanı tercih edilir.
