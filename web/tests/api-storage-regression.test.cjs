// Use dynamic ES module imports in this CommonJS test entry point.
async function registerTests() {
  const { default: fs } = await import('node:fs');
  const { default: assert } = await import('node:assert/strict');
  const { default: test } = await import('node:test');
  const { default: vm } = await import('node:vm');
  const { default: path } = await import('node:path');
  const { default: ts } = await import('typescript');
  const source = fs.readFileSync(path.resolve(__dirname, '../src/lib/api.ts'), 'utf8');
  const resolver = source.match(/const getApiBase = [\s\S]*?\n};/)[0];
  const code = ts.transpileModule(resolver+'\ngetApiBase();',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
  const resolve = ({host,storage,env={}}) => vm.runInNewContext(code,{...(host===undefined?{}:{window:{location:{hostname:host}}}),localStorage:storage,process:{env}});
  const denied={getItem(){throw new DOMException('Access denied','SecurityError')}};
  test('blocked storage on localhost uses local API',()=>assert.equal(resolve({host:'localhost',storage:denied}),'http://127.0.0.1:8000'));
  test('blocked storage on hosted UI uses configured API',()=>assert.equal(resolve({host:'example.invalid',storage:denied,env:{NEXT_PUBLIC_API_URL:'https://api.example.invalid'}}),'https://api.example.invalid'));
  test('blocked storage without env uses existing default',()=>assert.equal(resolve({host:'example.invalid',storage:denied}),'https://auren-api-8yrq.onrender.com'));
  test('saved override still takes precedence',()=>assert.equal(resolve({host:'localhost',storage:{getItem:()=> 'https://override.invalid///'}}),'https://override.invalid'));
  test('SSR does not access storage',()=>assert.equal(resolve({storage:denied,env:{NEXT_PUBLIC_API_URL:'https://api.example.invalid'}}),'https://api.example.invalid'));
}

registerTests().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
