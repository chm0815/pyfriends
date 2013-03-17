import sqlite3
import networkx as nx


def sqlite_connect():
    connection = sqlite3.connect("data")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return connection,cursor

def main():
    print "connecting..."
    connection,cursor = sqlite_connect()
    print "connection established!"
    
    print "creating social network..."
    G=nx.Graph()
    for row in cursor.execute('SELECT p.url as purl,f.friendurl as furl FROM friends f inner join persons p on f.personid=p.personid'):
        #print "purl=%s furl=%s" % (row["purl"],row["furl"])
        G.add_edge(row["purl"],row["furl"])
    connection.rollback()
    connection.close()
    print "social network successfull created!"
    
    path = nx.shortest_path(G, "<url_from>", "<url_to>", weight=1)
    
    print path
    
if __name__ == '__main__':
    main()   