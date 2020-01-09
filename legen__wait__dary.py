import time

print ("Legen....")
time.sleep(1)
print (".wait.")
time.sleep(1)

strat=[1,2,3,7]
optdate=[10,15,18,19]
optnum=[50, 52, 56]

def sqlexec(sql, *args):
  fd = open(sql, 'r')
  sql_query = fd.read()
  fd.close()
  #for a in range(0,len(args)):
    #print(a)
  valid_sql_query = sql_query.format(*args)
									#strat   = args[a],
									#optdate   = args[a+1]
									#optnum  = args[2]
									#)
  return valid_sql_query									

print (sqlexec('legen_sql.sql', strat, optdate, optnum))



print ("....wait....")
time.sleep(1)
print ("............dary!!!")

