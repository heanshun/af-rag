from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-small-zh')
sentence = "你好，我想问一下产品怎么用？"
embedding = model.encode(sentence, normalize_embeddings=True)

print(embedding.shape)  # 输出向量维度
print(embedding) # 输出向量
