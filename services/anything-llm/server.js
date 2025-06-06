const express = require("express");
const dotenv = require("dotenv");
const axios = require("axios");
dotenv.config();

const app = express();
app.use(express.json());

app.post("/ask", async (req, res) => {
  const prompt = req.body.prompt;
  try {
    const response = await axios.post(`${process.env.OLLAMA_HOST}/api/generate`, {
      model: process.env.OLLAMA_MODEL || "llama3",
      prompt,
      stream: false
    });
    res.json({ answer: response.data.response });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "LLM generation failed" });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Anything-LLM listening on port ${PORT}`));
