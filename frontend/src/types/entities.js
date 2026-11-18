/** @typedef {{id:number,name:string,note:string,status:string,publish_seq:number|null,affected_from:string|null,diff:Array,recomputed:Array,op_count:number,created_at:string,published_at:string|null}} Revision */
/** @typedef {{id:number,up_to_hour:string,status:string,watermark:number|null,result:Object|null,error:string|null,delay_seconds:number,created_at:string,finished_at:string|null}} Settlement */
/** @typedef {{hour:string,peak:number,start:number,end:number,start_keys?:Array,end_keys?:Array,source?:string}} HourPeak */
export const entityNames={revision:'修订批次',settlement:'结算任务',peak:'小时峰值'};
