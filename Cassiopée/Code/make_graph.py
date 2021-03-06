import MySQLdb as mdb
import pandas as pd
import pandas.io.sql as psql
import matplotlib.pyplot as plt
import tkinter
import os

def list():
    print()
    print('Voici la liste des graphes disponibles: ')
    print("1. Répartition des advisories par secteur")
    print("2. Nombre de CVE par advisory")
    print("3. Répartition des CVE par SFP2")
    print("4. Répartition des CVE par SFP1")


def autolabel(rects, xpos='center'):
    """
    Attach a text label above each bar in *rects*, displaying its height.

    *xpos* indicates which side to place the text w.r.t. the center of
    the bar. It can be one of the following {'center', 'right', 'left'}.
    """

    ha = {'center': 'center', 'right': 'left', 'left': 'right'}
    offset = {'center': 0, 'right': 1, 'left': -1}

    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(offset[xpos] * 3, 3),  # use 3 points offset
                    textcoords="offset points",  # in both directions
                    ha=ha[xpos], va='bottom')

#Fonction permettant d'exporter au format csv si les conditions le permettent
def export_to_csv(i, csv, df):
    if csv == 'csv':
        df.to_csv('export_graph{}.csv'.format(i))
        print('L\'export en .csv a été correctement réalisé. Retrouvez dans le dossier {}'.format(os.getcwd()))
    else:
        print('Aucun export en .csv n\'a été fait. Pour exporter en .csv, tapez csv après le graphe de votre choix.')


def graph(i, mdp, csv):
    db = mdb.Connection(host='localhost', db='cassiopee', passwd=mdp, user='root', charset='utf8')


    if(i == '1'):
        query_sector = "select * from sector_instances"

        df_sector = psql.read_sql(query_sector, con=db)

        df_sector.plot(x='sname',
                       y='quantity',
                       kind='bar',
                       title='Number of products per sector'
                       )

        export_to_csv(i, csv, df_sector)

        plt.show()

    if(i == '2'):
        query_sector = "select * from icscert_instances"

        df_sector = psql.read_sql(query_sector, con=db)

        df_sector.plot(x='icscert',
                       y='quantity',
                       kind='bar',
                       title='Number of CVE per ICSCERT'
                       )

        export_to_csv(i, csv, df_sector)


        plt.show()

    if(i == '3'):
        query_sector = "select * from sfp2_instances"

        df_sector = psql.read_sql(query_sector, con=db)

        df_sector.plot(x='sfp2',
                       y='quantity',
                       kind='bar',
                       title='Number of CVE per SFP2'
                       )

        export_to_csv(i, csv, df_sector)

        plt.show()

    if(i == '4'):
        query_sector = "select * from sfp1_instances"

        df_sector = psql.read_sql(query_sector, con=db)

        df_sector.plot(x='sfp1',
                       y='quantity',
                       kind='bar',
                       title='Number of CVE per SFP1'
                       )

        export_to_csv(i, csv, df_sector)

        plt.show()
