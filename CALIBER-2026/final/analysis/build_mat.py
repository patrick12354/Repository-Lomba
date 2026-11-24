import sys;sys.path.insert(0,'analysis');from load import *;import pandas as pd, numpy as np
def build():
    bom,fl,mp,mv,nt,pp=load()
    rank={'A':4,'B':3,'C':2,'S':1}   # committee (TM 4 Nov): A highest, order A>B>C>S
    b=bom.merge(fl,left_on='Functional Loc.',right_on='Functional Location',how='left')
    b['crit_r']=b['FuncLoc Criticallity'].map(rank)
    m=b.groupby('Material No').agg(desc=('Material Desc.','first'),unit=('Unit','first'),mrp=('MRP Type','first'),
        stock=('Stock','first'),mn=('Min.Qty','first'),mx=('Max.Qty','first'),n_fl=('Functional Loc.','nunique'),
        inst=('Installed Qty','sum'),crit_r=('crit_r','max')).reset_index()
    m['crit']=m.crit_r.map({v:k for k,v in rank.items()})
    m['cat']=m.desc.str.split(',').str[0]
    # consumption
    end=mv['Posting Date'].max(); start=mv['Posting Date'].min(); months=(end-start).days/30.44
    c=mv.groupby('Material Number').agg(qty=('Quantity','sum'),n_iss=('Quantity','size'),last=('Posting Date','max'),n_ord=('Order','nunique'))
    m=m.merge(c,left_on='Material No',right_index=True,how='left')
    m[['qty','n_iss','n_ord']]=m[['qty','n_iss','n_ord']].fillna(0)
    m['mon_dem']=m.qty/months
    # price (IDR only for unit price), lead time
    p=pp.copy()
    # PO-Item Amount behaves as a UNIT price: within a material it barely varies (CV~2%) and is
    # uncorrelated with PR-Quantity (r=0.03). Line value = amount x quantity.
    p['unit_px']=p['PO-Item Amount']; p['line_val']=p['PO-Item Amount']*p['PR-Quantity']
    p['lt_days']=(p['PO-Delivery Date']-p['PR-Date']).dt.days
    p['slip']=(p['PO-Delivery Date']-p['PR-Delivery Date']).dt.days
    pi=p[p['PO-Currency']=='IDR'].groupby('PR-Material').agg(px=('unit_px','median'))
    pl=p.groupby('PR-Material').agg(lt_med=('lt_days','median'),lt_p90=('lt_days',lambda s:s.quantile(.9)),n_pr=('Purchase Requisition','nunique'),pr_qty=('PR-Quantity','sum'),spend=('line_val','sum'),n_sup=('PO-Supplier Code','nunique'))
    m=m.merge(pi,left_on='Material No',right_index=True,how='left').merge(pl,left_on='Material No',right_index=True,how='left')
    return m,(bom,fl,mp,mv,nt,pp,p),months
