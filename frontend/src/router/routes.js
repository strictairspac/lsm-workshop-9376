export const routes=[['datasets','01','写入批次'],['configs','02','层级配置'],['trials','03','合并队列'],['report','04','读放大证据']];export const current=()=>location.hash.slice(1).split('/')[0]||'datasets';
