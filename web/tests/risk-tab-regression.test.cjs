// Use dynamic ES module imports in this CommonJS test entry point.
async function registerTests() {
  const { default: fs } = await import('node:fs');
  const { default: assert } = await import('node:assert/strict');
  const { default: test } = await import('node:test');
  const { default: vm } = await import('node:vm');
  const { default: path } = await import('node:path');
  const { default: ts } = await import('typescript');
  const source = fs.readFileSync(path.resolve(__dirname, '../src/components/dashboard/Workstation.tsx'), 'utf8');
  const start = source.indexOf('{activeTab === "risk-analysis"');
  const end = source.indexOf('{/* ANALYTICS Sections */}',start);
  assert.ok(start >= 0 && end > start, 'Risk Analysis tab branch exists');
  const code = ts.transpileModule('const element = <> '+source.slice(start,end)+' </>; element;',{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.React}}).outputText;
  const renderTab=(activeTab,loading=false)=>{
   const calls=[]; const handler=()=>{}; const simulation={result:{score:20}}; const error='sample';
   const ctx={activeTab,loading,handleSimulate:handler,data:{score:30},simulation,error,StressView:'StressView',MarketOverviewView:'MarketOverviewView',React:{Fragment:'Fragment',createElement:(component,props,...children)=>{const node={component,props,children};calls.push(node);return node;}}};
   vm.runInNewContext(code,ctx);
   return {view:calls.find(x=>x.component==='StressView'),handler,simulation,error,calls};
  };
  test('risk analysis passes actual recalculation callback',()=>{const r=renderTab('risk-analysis');assert.equal(r.view.props.onSimulate,r.handler)});
  test('risk analysis forwards busy flag',()=>assert.equal(renderTab('risk-analysis',true).view.props.isSimulating,true));
  test('risk analysis forwards comparison and error',()=>{const r=renderTab('risk-analysis');assert.equal(r.view.props.simulation,r.simulation);assert.equal(r.view.props.error,r.error)});
  test('other tab does not mount risk analysis',()=>assert.equal(renderTab('market-overview').view,undefined));
}

registerTests().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
