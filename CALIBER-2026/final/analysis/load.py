import pandas as pd
D='data/'
def load():
    bom=pd.read_excel(D+'BoM.xlsx'); fl=pd.read_excel(D+'FuncLoc list.xlsx')
    mp=pd.read_excel(D+'Mitem & Mplan.xlsx'); mv=pd.read_excel(D+'Movement Material.xlsx')
    nt=pd.read_excel(D+'Notif History.xlsx')
    pp=pd.read_excel(D+'PR PO.xlsx').drop_duplicates()   # 5,420 of 11,609 lines are exact duplicates; PR+item is unique after this
    return bom,fl,mp,mv,nt,pp
