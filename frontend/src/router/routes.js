export const routes=[['peaks','01','峰值总览'],['revisions','02','修订批次'],['settlements','03','结算队列']];export const current=()=>location.hash.slice(1).split('/')[0]||'peaks';
