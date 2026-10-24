// @vitest-environment jsdom
import {it,expect,afterEach} from 'vitest';
import {availability,isCurrentResult,methodFor,loadViewState,type CapabilityResponse,type ResultIdentity} from './analysis-workflow';
import type {EditableModelDocument} from './types';
const doc=(metadata={})=>({components:[{category:'column'},{category:'column'},{category:'beam'},{category:'slab'}],metadata}) as unknown as EditableModelDocument;
const identity:ResultIdentity={id:1,project_id:7,model_revision_id:2,method:'frame',status:'VERIFIED',load_cases:['Gravity'],model_document_sha256:'hash'};
afterEach(()=>localStorage.clear());
it('component counts and metadata cannot grant support without backend evidence',()=>{expect(availability('structure',doc()).available).toBe(false);expect(availability('floors',doc({coupled_floor_review:{}})).available).toBe(false);});
it('uses backend status and explanation',()=>{const capabilities={methods:{frame:{status:'UNSUPPORTED',reason:'Unsupported geometry',can_review:false,current_results:[],history:[]}}} as unknown as CapabilityResponse;expect(availability('structure',doc(),capabilities)).toEqual({available:false,status:'UNSUPPORTED',reason:'Unsupported geometry'});});
it('binds project, revision, method, result and backend status',()=>{const row={id:1,model_revision_id:2,status:'VERIFIED',result:{run_id:'native',model_document_sha256:'hash'}};expect(isCurrentResult(row,2,identity,7,'frame')).toBe(true);for(const changed of [{project_id:8},{model_revision_id:3},{method:'slab' as const},{id:2},{status:'STALE'},{load_cases:[]},{model_document_sha256:'wrong'}])expect(isCurrentResult(row,2,{...identity,...changed},7,'frame')).toBe(false);expect(isCurrentResult(row,2)).toBe(false);});
it('retains routing and valid browser preferences without authorization',()=>{expect(methodFor('floors',doc({spatial_frame_review:{}}))).toBe('spatial');localStorage.setItem('view',JSON.stringify({family:'floors',step:'results',mode:'slab',caseName:'Gravity'}));expect(loadViewState('view')?.step).toBe('results');localStorage.setItem('view','invalid');expect(loadViewState('view')).toBeNull();});
