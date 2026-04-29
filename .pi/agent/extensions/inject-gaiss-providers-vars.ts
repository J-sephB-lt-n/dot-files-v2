export default function (pi: any) {
  pi.registerProvider("gaiss", {
    baseUrl: process.env.OPENAI_BASE_URL,
    apiKey: process.env.OPENAI_API_KEY,
  });
}
