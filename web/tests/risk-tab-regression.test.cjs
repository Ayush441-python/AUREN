const fs = require('node:fs');
const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const path = require('node:path');
const cp = require('node:child_process');
let ts; try { ts = require('typescript'); } catch { ts = require(path.join(cp.execSync('npm root -g',{encoding:'utf8'}).trim(),'typescript')); }
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
