import csv,sqlite3
SCHEMA='create table if not exists requests(id text primary key,model text,input_tokens integer,output_tokens integer,cost_usd real,status text)'
def init(path): sqlite3.connect(path).execute(SCHEMA)
def record(path,row):
 with sqlite3.connect(path) as c:c.execute(SCHEMA);c.execute('insert or replace into requests values (?,?,?,?,?,?)',row)
def export(path,out):
 with sqlite3.connect(path) as c: rows=c.execute('select * from requests').fetchall()
 with open(out,'w',newline='') as f: w=csv.writer(f);w.writerow(['id','model','input_tokens','output_tokens','cost_usd','status']);w.writerows(rows)
