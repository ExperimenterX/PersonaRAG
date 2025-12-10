<script setup>
import ChatWidget from './components/ChatWidget.vue'
</script>

<template>
  <div class="page">
    <header class="hero">
      <div class="hero-inner">
        <h1>Bhavani Shankar</h1>
        <p class="hero-subtitle">
          MSCS @ UIC · Ex-Bosch Senior Software Engineer · Specializing in AI, RAG Systems & Cloud Architecture
        </p>
        <p class="hero-body">
          Welcome to <strong>PersonaRAG</strong> – an intelligent AI assistant powered by Retrieval-Augmented Generation.
          This system combines FastAPI, FAISS vector search, and LLM technology to provide contextual answers about my
          professional background. Try asking questions in the <strong>chat widget below</strong>! 💬
        </p>
      </div>
    </header>

    <main class="content">
      <section class="card">
        <h2>🎓 About Me</h2>
        <p>
          I'm pursuing my Master's in Computer Science at the University of Illinois Chicago (graduating May 2026),
          with coursework in Responsible AI, NLP, Information Retrieval, and Advanced Software Engineering.
          Previously, I worked as a Senior Software Engineer at Bosch Global Software Technologies in Bangalore,
          where I built high-performance systems using Golang, Python, and cloud technologies.
        </p>
      </section>

      <section class="card">
        <h2>💼 Professional Experience</h2>
        <ul>
          <li><strong>Graduate Assistant @ UIC</strong> – Building web applications for the College of Engineering using React, Node.js, and MySQL</li>
          <li><strong>Senior Software Engineer @ Bosch</strong> – Implemented task manager services in Golang, reducing processing time by 15%</li>
          <li><strong>Software Engineer @ Bosch</strong> – Engineered validation framework that cut manual testing from 4 days to 5 hours</li>
          <li>Designed SQL-driven REST APIs with OAuth2, boosting data handling efficiency by 30%</li>
        </ul>
      </section>

      <section class="card">
        <h2>🚀 Featured Projects</h2>
        <ul>
          <li><strong>PersonaRAG</strong> – This application! RAG pipeline with FAISS vector search, BGE reranking, and FastAPI backend</li>
          <li><strong>SyncAI</strong> – AI-powered student assistant with multi-stage retrieval and AWS integration</li>
          <li><strong>QueryMind</strong> – LangChain-based engine with custom retrievers and context-aware reranking</li>
          <li><strong>Grocery Price Compare</strong> – Real-time price tracking across multiple stores with data visualization</li>
        </ul>
      </section>

      <section class="card">
        <h2>🛠️ Technical Skills</h2>
        <div class="skills-grid">
          <div>
            <strong>Languages:</strong> Python, Golang, JavaScript, TypeScript, SQL
          </div>
          <div>
            <strong>AI/ML:</strong> LLMs, RAG Systems, NLP, LangChain, FAISS, Sentence Transformers
          </div>
          <div>
            <strong>Cloud:</strong> AWS, Azure, GCP, Docker, Kubernetes, CI/CD
          </div>
          <div>
            <strong>Frameworks:</strong> FastAPI, React, Vue.js, Node.js, Express.js, Flask
          </div>
        </div>
      </section>

      <section class="card">
        <h2>🎯 What PersonaRAG Does</h2>
        <p>
          This application demonstrates a production-ready RAG system with:
        </p>
        <ul>
          <li><strong>Hybrid Retrieval</strong> – Combines dense (FAISS) and sparse (BM25) search for optimal results</li>
          <li><strong>Cross-Encoder Reranking</strong> – BGE reranker improves relevance of retrieved contexts</li>
          <li><strong>Real-time Chat Interface</strong> – Vue.js frontend with typing animations and error handling</li>
          <li><strong>FastAPI Backend</strong> – High-performance Python API with CORS support and lazy loading</li>
          <li><strong>Document Indexing</strong> – Processes resume data and PDF documents into searchable chunks</li>
        </ul>
        <p class="tech-note">
          <em>Tech Stack: Python 3.11, FastAPI, FAISS, Haystack, Sentence Transformers, Vue 3, Vite</em>
        </p>
      </section>

      <section class="card highlight-card">
        <h2>💬 Try the AI Assistant!</h2>
        <p>
          Click the chat widget in the bottom-right corner to ask questions like:
        </p>
        <ul class="example-queries">
          <li>"What programming languages does Bhavani know?"</li>
          <li>"Tell me about his experience at Bosch"</li>
          <li>"What certifications does he have?"</li>
          <li>"Describe his AI/ML projects"</li>
        </ul>
        <p class="tech-note">
          The assistant uses GPT-based generation with retrieval from 33+ certifications, education history,
          work experience, and project documentation.
        </p>
      </section>

    <p style="font-style: italic; font-weight: bold; text-align: center; margin: 2rem 0; font-size: 1.1rem; color: #475569;">"A static web page to introduce you to PersonaRAG - Bhavani Shankar's personal AI assistant who can answer any queries you have about him"</p>
    </main>

    <!-- Floating Chat -->
    <ChatWidget />
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(to bottom, #f9fafb 0%, #ffffff 100%);
}

.hero {
  background: radial-gradient(circle at top left, #5fc68c 0%, #6a62d6 60%, #973a51 100%);
  color: white;
  padding: 1rem 1.5rem 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.hero-inner {
  max-width: 1000px;
  margin: 0 auto;
}

.hero h1 {
  font-size: 2.8rem;
  margin-bottom: 0.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 1.1rem;
  opacity: 0.95;
  margin-bottom: 1.2rem;
  font-weight: 500;
}

.hero-body {
  font-size: 1rem;
  max-width: 680px;
  line-height: 1.7;
  opacity: 0.92;
}

.content {
  max-width: 1000px;
  margin: 2rem auto 4rem;
  padding: 0 1.5rem 5rem;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1.8rem;
}

.card {
  background: white;
  border-radius: 18px;
  padding: 1.8rem 2rem;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.12);
}

.card h2 {
  font-size: 1.4rem;
  margin-bottom: 1rem;
  color: #1e293b;
  font-weight: 600;
}

.card p {
  font-size: 1rem;
  line-height: 1.7;
  color: #475569;
  margin-bottom: 0.8rem;
}

.card li {
  font-size: 0.98rem;
  line-height: 1.8;
  color: #475569;
  margin-bottom: 0.5rem;
}

.card ul {
  padding-left: 1.5rem;
}

.skills-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.9rem;
  margin-top: 0.8rem;
}

.skills-grid > div {
  padding: 0.8rem 1rem;
  background: #f8fafc;
  border-radius: 10px;
  border-left: 3px solid #4f46e5;
  font-size: 0.95rem;
  line-height: 1.6;
}

.skills-grid strong {
  color: #1e293b;
  display: block;
  margin-bottom: 0.3rem;
}

.tech-note {
  margin-top: 1rem;
  padding: 0.8rem 1rem;
  background: #fef3c7;
  border-radius: 10px;
  font-size: 0.9rem;
  color: #78350f;
  border-left: 3px solid #f59e0b;
}

.highlight-card {
  background: linear-gradient(135deg, #eef2ff 0%, #f9fafb 100%);
  border: 2px solid #4f46e5;
}

.example-queries {
  background: white;
  padding: 1rem 1.2rem;
  border-radius: 10px;
  margin: 1rem 0;
}

.example-queries li {
  color: #4f46e5;
  font-style: italic;
}

@media (min-width: 768px) {
  .skills-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .hero h1 {
    font-size: 3.2rem;
  }
}
</style>
