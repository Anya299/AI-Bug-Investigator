export function detectFromStackTrace(stack) {

  let language = "";
  let framework = "";

  const text = stack.toLowerCase();

  if (text.includes(".py") || text.includes("traceback")) {
    language = "Python";
  }

  if (text.includes("fastapi")) {
    framework = "FastAPI";
  }

  if (text.includes("django")) {
    framework = "Django";
  }

  if (text.includes(".js") || text.includes("node")) {
    language = "JavaScript";
  }

  if (text.includes("react")) {
    framework = "React";
  }

  if (text.includes(".java")) {
    language = "Java";
  }

  return {
    language,
    framework
  };
}