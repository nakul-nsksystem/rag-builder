import express, { Request, Response } from 'express';
import cors from 'cors';
import { QdrantClient } from '@qdrant/js-client-rest';
import { ChatOpenAI } from 'langchain/chat_models/openai';
import { RetrievalQAChain } from 'langchain/chains';
import { PromptTemplate } from 'langchain/prompts';
import * as dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

interface Config {
  llmType: string;
  llmEndpoint: string;
  llmModel: string;
  llmTemperature: number;
  systemPrompt: string;
  openaiApiKey?: string;
  embeddingModel: string;
  qdrantPath: string;
  collectionName: string;
  apiPort: number;
}

const config: Config = {
  llmType: process.env.LLM_TYPE || 'lm_studio',
  llmEndpoint: process.env.LLM_ENDPOINT || 'http://192.168.0.194:1234/v1',
  llmModel: process.env.LLM_MODEL || 'llama-3',
  llmTemperature: parseFloat(process.env.LLM_TEMPERATURE || '0.2'),
  systemPrompt: process.env.SYSTEM_PROMPT || 'You are a helpful assistant that answers questions based on the provided context. Only answer based on the context provided. If you cannot find the answer, say so. Be concise and accurate.',
  openaiApiKey: process.env.OPENAI_API_KEY,
  embeddingModel: process.env.EMBEDDING_MODEL || 'BAAI/bge-m3',
  qdrantPath: process.env.QDRANT_PATH || './vectors/qdrant',
  collectionName: process.env.COLLECTION_NAME || 'rag_collection',
  apiPort: parseInt(process.env.API_PORT || '8000'),
};

const qdrant = new QdrantClient({ url: config.qdrantPath });

const llm = new ChatOpenAI({
  model: config.llmModel,
  openAIApiKey: config.openaiApiKey || 'not-needed',
  temperature: config.llmTemperature,
  maxTokens: 500,
  configuration: {
    baseURL: config.llmType !== 'openai' ? config.llmEndpoint : undefined,
  },
});

interface QueryRequest {
  query: string;
  top_k?: number;
}

interface QueryResponse {
  answer: string;
  sources: Array<{
    content: string;
    source: string;
  }>;
  question: string;
}

app.get('/health', (_req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    vector_db: 'qdrant',
    embedding_model: config.embeddingModel,
    llm_type: config.llmType,
  });
});

app.post('/rag/query', async (req: Request<{}, {}, QueryRequest>, res: Response<QueryResponse>) => {
  const { query, top_k = 5 } = req.body;

  try {
    const searchResults = await qdrant.search(config.collectionName, {
      limit: top_k,
      vector: new Array(1024).fill(0),
      filter: {},
    });

    const context = searchResults.map((r: any) => r.payload?.text || '').join('\n\n');

    const prompt = PromptTemplate.fromTemplate(
      `${config.systemPrompt}\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:`
    );

    const chain = RetrievalQAChain.fromLLM(llm, null as any, {
      prompt: await prompt.format({ context, question: query }),
    });

    const result = await chain.call({ query });

    const sources = searchResults.map((r: any) => ({
      content: (r.payload?.text || '').substring(0, 300) + '...',
      source: r.payload?.source || 'unknown',
    }));

    res.json({
      answer: result.text || result.result || 'No response',
      sources,
      question: query,
    });
  } catch (error: any) {
    console.error('Error:', error);
    res.status(500).json({
      answer: `Error: ${error.message}`,
      sources: [],
      question: query,
    });
  }
});

app.post('/rag/ingest', async (_req: Request, res: Response) => {
  res.json({ status: 'success', message: 'Re-ingest not implemented in TypeScript yet' });
});

const PORT = config.apiPort;
app.listen(PORT, () => {
  console.log(`RAG API running on port ${PORT}`);
});

export default app;