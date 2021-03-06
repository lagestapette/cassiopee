﻿from bs4 import BeautifulSoup
import urllib.request
import re
import MySQLdb as mdb
import ssl

"""
ICS-CERT n'accepte pas les requetes ne venant pas de navigateurs,
on change alors le User-Agent de nos requetes pour se faire passer
pour Mozilla Firefox:
"""
class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"


# Crée une instance d'opener d'url avec le bon User-Agent
opener = AppURLopener()


class Advisory:
    def send_to_db(self):

        db = mdb.Connection(host='localhost', db='cassiopee', passwd=self.mdp, user='root', charset='utf8')
        c = db.cursor()

        #Insertion d'une valeur par défaut pour le patch
        c.execute(""" insert ignore into patch values(DEFAULT , 'Default Patch Name') """)

        db.commit()

        #Récupération de l'id du patch de l'Advisory courant
        c.execute(""" select id from patch where patch='Default Patch Name'  """)
        patch_id = c.fetchone()

        #Remplissage de la table ICS-CERT
        c.execute(""" insert into icscert values (default , %s, %s, %s)""", (self.ics_date, patch_id[0], self.ics))

        db.commit()

        #Récupération de l'id de l'ics courant
        c.execute(""" select id from icscert where name=%s """, (self.ics,))
        icscert_id = c.fetchone()

        #Parcourir tous les CVE de l'advisory courant pour remplir les SFP1/2, CWE et CVSS
        if len(self.cve) == len(self.sfp1) == len(self.cvss) and self.ics!='ICSA-18-345-02' and self.ics!='ICSA-18-228-01':
            for i in range(len(self.cve)):

                c.execute(""" insert ignore into sfp1 values (default , %s)""", (self.sfp1[i],))

                db.commit()

                c.execute(""" select id from sfp1 where name=%s """, (self.sfp1[i],))
                sfp1_id = c.fetchone()

                c.execute(""" insert ignore into sfp2 values (default , %s, %s)""", (self.sfp2[i], sfp1_id[0]))

                db.commit()

                c.execute(""" select id from sfp2 where name=%s """, (self.sfp2[i],))
                sfp2_id = c.fetchone()

                c.execute(""" insert into cwe values (default , %s, %s, %s, %s, %s)""", (self.cwe_link[i],
                                                                                         self.abstraction[i],
                                                                                         self.structure[i],
                                                                                         sfp2_id[0],
                                                                                         self.cwe[i]))

                cwe_id = c.lastrowid
                c.execute(""" insert ignore into cvss values (default, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (self.cvss[i][0][-1],
                                                                                                         self.cvss[i][1][-1],
                                                                                                         self.cvss[i][2][-1],
                                                                                                         self.cvss[i][3][-1],
                                                                                                         self.cvss[i][4][-1],
                                                                                                         self.cvss[i][5][-1],
                                                                                                         self.cvss[i][6][-1],
                                                                                                         self.cvss[i][7][-1],
                                                                                                         self.score[i]))

                db.commit()

                c.execute(""" select id from cvss where 
                av = %s and 
                ac = %s and 
                pr = %s and 
                ui = %s and 
                s = %s and 
                c = %s and 
                i = %s and 
                a = %s """,
                          ((self.cvss[i][0][-1],
                            self.cvss[i][1][-1],
                            self.cvss[i][2][-1],
                            self.cvss[i][3][-1],
                            self.cvss[i][4][-1],
                            self.cvss[i][5][-1],
                            self.cvss[i][6][-1],
                            self.cvss[i][7][-1])))
                cvss_id = c.fetchone()
                c.execute(""" insert into cve values (default , %s, %s, %s, %s, %s, %s)""", (self.cve_date[i],
                                                                                                 cvss_id[0],
                                                                                                 cwe_id,
                                                                                                 self.cve[i],
                                                                                                 self.cve_link[i],
                                                                                                 self.cve_date_publi[i]))

                db.commit()

                c.execute(""" select id from cve where name=%s """, (self.cve[i],))
                cve_id = c.fetchone()

                c.execute(""" insert ignore into icscert_cve values (default , %s, %s)""", (icscert_id[0], cve_id[0]))

        else:
            print('L\'entrée %s est un cas particulier qui ne peut pas encore être traité.', (self.ics,))
            return 0

        #Remplissage des informations du vendeur
        c.execute(""" insert ignore into vendor values(DEFAULT , %s, %s) """, (self.location, self.vendor))

        #Remplissage par défaut du type de device
        c.execute(""" insert ignore into devicetype values (default , 'type')""")

        db.commit

        c.execute(""" select id from devicetype where type='type' """)
        devicetype_id = c.fetchone()

        c.execute(""" select id from vendor where name = %s """, (self.vendor,))
        vendor_id = c.fetchone()

        #Remplissage des informations du produit concerné par l'advisory
        c.execute(""" insert into product values (default , %s, 0, %s, 'Device Comment', %s)""", (self.product,
                                                                                                  devicetype_id[0],
                                                                                                  vendor_id[0]))

        db.commit()

        #Récupération de l'id du produit courant
        c.execute(""" select id from product where name = %s """, (self.product,))
        product_id = c.fetchone()

        #Parcours de tous les secteurs de l'advisory courant
        for i in range(len(self.sector)):
            c.execute(""" insert ignore into sector values (default , %s) """, (self.sector[i],))
            db.commit()
            c.execute(""" select id from sector where name = %s """, (self.sector[i],))
            sector_id = c.fetchone()
            c.execute(""" insert ignore into product_sector values (default , %s, %s)""", (product_id[0], sector_id[0]))

        #Parcours de tous les pays où le produit a été déployé, avec remplissage si le pays n'existe pas déjà en base
        for i in range(len(self.countries)):
            c.execute(""" select id from countries where name like %s """, ('%' + self.countries[i] + '%',))
            countries_id_tuple = c.fetchone()
            if countries_id_tuple is None:
                c.execute(""" insert into countries values (default , null , %s)""", (self.countries[i],))
                countries_id = c.lastrowid
                db.commit()
            else:
                countries_id = countries_id_tuple[0]
            c.execute(""" insert ignore into product_countries values (default , %s, %s)""", (product_id[0],
                                                                                              countries_id))

        #remplissage de la table de jointure entre ICS et Produit
        c.execute(""" insert into icscert_product values (default , %s, %s)""", (icscert_id, product_id))

        db.commit()

        c.close()
        db.close()


        # Print
        print(self.ics + " mis en base")

    def __init__(self,url, mdp):
        self.mdp = mdp

        # Récupération du code html de l'url de l'advisory
        page = opener.open(url)
        self.soup = BeautifulSoup(page, 'html.parser')

        # Référence de l'advisory ICS-CERT
        self.ics = self.parser('h1', 'Advisory', "[A-Za-z\s]*\(")

        # Date de publication originale de l'advisory (mis au format YYYY-MM-DD)
        date = self.parser('footer', 'date', "[A-Za-z\s]*: ").split(', ')
        date[0] = date[0].split(" ")
        date[1] = date[1].split(" ")
        if date[0][0] == "January": date[0][0] = "01"
        elif date[0][0] == "February": date[0][0] = "02"
        elif date[0][0] == "March": date[0][0] = "03"
        elif date[0][0] == "April": date[0][0] = "04"
        elif date[0][0] == "May": date[0][0] = "05"
        elif date[0][0] == "June": date[0][0] = "06"
        elif date[0][0] == "July": date[0][0] = "07"
        elif date[0][0] == "August": date[0][0] = "08"
        elif date[0][0] == "September": date[0][0] = "09"
        elif date[0][0] == "October": date[0][0] = "10"
        elif date[0][0] == "November": date[0][0] = "11"
        elif date[0][0] == "December": date[0][0] = "12"
        self.ics_date = date[1][0] + '-' + date[0][0] + '-' + date[0][1]

        # Entreprise qui vend le produit
        self.vendor = self.parser_parent("Vendor")

        # Localisation de l'entreprise
        self.location = self.parser_parent("LOCATION")

        # Nom du produit
        self.product = self.parser_parent("Equipment").replace(";",",")

        # Liste des secteurs d'activité auxquels appartient le produit
        self.sector = self.parser_parent("SECTORS").replace('•','').replace('/',',').replace(', and ',',').replace(' and ',',').replace(";",",").replace(', ',',').split(",")
        for i in range(len(self.sector)):
            self.sector[i] = self.sector[i].rstrip()
            self.sector[i] = self.sector[i].rstrip('.')
            self.sector[i] = self.sector[i].replace('CRITICAL INFRASTRUCTURE SECTORS: ','')
            self.sector[i] = self.sector[i].replace('Communications','Communication')
            self.sector[i] = self.sector[i].replace('Multiple sectors', 'Multiple')
            self.sector[i] = self.sector[i].replace('andWater','Water')
            self.sector[i] = re.sub("[A-Za-z0-9\s]*Worldwide[A-Za-z0-9\s]*", "", self.sector[i])

        # Pays où le produit est disponible
        self.countries = self.parser_parent("DEPLOYED").replace(";",",").split(", ")


        # Liste des CVE (possibilité d'avoir plusieurs CVE par advisory)
        self.cve = []

        # Liste des liens vers NVD
        self.cve_link = []

        # Liste des dates de créations des CVE (1er janvier de l'année répertoriée)
        self.cve_date = []

        # Liste des dates de publication des CVE sur NVD(1er Janvier si date précise non disponible)
        self.cve_date_publi = []

        # Liste des descriptions des vulnérabilités
        #self.cve_text = []

        # Remplie les 4 listes précédentes
        self.cve_parser()


        # Liste des listes des vecteurs CVSS splités (possibilité d'avoir plusieurs CVSS par advisory)
        self.cvss = []

        # Liste des scores cvss
        self.score = []

        # Remplie les 2 listes précédentes
        self.cvss_parser()

        # Liste des références CWE (possibilité d'avoir plusieurs CWE par advisory)
        self.cwe = []

        # Liste des liens CWE
        self.cwe_link = []

        # Liste des abstractions répertoriées pour chaque CWE
        self.abstraction = []

        # Liste des structures répertoriées pour chaque CWE
        self.structure = []

        # Liste des arborescences SFP1 pour chaque vulnérabilité
        self.sfp1 = []

        # Liste des arborescences SFP2 pour chaque vulnérabilité
        self.sfp2 = []

        # Remplie les 6 listes précédentes
        self.cwe_parser()


    def parser(self,balise,target,clean,):
        """
        Récupère l'information voulue --> pour ref ics et date ics

        :param balise: balise html utilisée pour l'information

        :param target: expression reguliere pour trouver l'information

        :param clean: expression reguliere pour enlever les informations superflues recuperees

        :return: retourne l'information voulue
        """
        res = self.soup.find(balise, text=re.compile(target))
        res = res.getText()
        res = re.sub(clean, "", res)
        res = re.sub("\)", "", res)
        return res


    def parser_parent(self,exp):
        """
        Récupère l'information voulue --> pour l'entreprise, sa localisation, le produit, ses secteurs
        et les pays où il est déployé

        Fonction différente de la précédente : on passe par la balise enfant pour ces informations (toujours Strong)

        :param exp: expression régulière pour récupérer l'information voulue

        :return: retourne l'information voulue
        """
        res = self.soup.find('strong', text=re.compile(exp))

        # Problème si la syntaxe usuelle n'est pas respectée --> renvoie None dans ce cas
        if res != None:
            res = res.parent
            res = res.getText()
            res = re.sub("[A-Za-z0-9/\s]*:[\s]*", "", res)
        else:
            res = "Inconnu"
        return res


    def parser_cve_date_publi(self,cve):
        """
        Récupère la date de publication d'un CVE si celle-ci est disponible

        :param cve: CVE dont on veut la date

        :return: retourne la date de création du CVE
        """
        try:
            pageCVE = opener.open(cve.get('href'))
        except(ssl.CertificateError) as e:
            return None
        soupCVE = BeautifulSoup(pageCVE, 'html.parser')
        res = soupCVE.find('strong', text=re.compile("Last Modified"))
        if res != None:
            res = res.next_sibling.next_sibling.next_sibling
            res = res.getText()
            res = re.sub("[A-Za-z0-9/\s]*: ", "", res)
            res = res.split("/")
            res = res[2] + '-' + res[0] + '-' + res[1]
            return res
        return None


    def cve_parser(self):
        """
        Récupère les CVE, leurs liens vers NVD, dates de création, et les texte associées chaque vulnérabilité

        Remplie les listes initialisées au préalable (voir fonction __init__ ci-dessus)
        """
        cves = self.soup.findAll('a', text=re.compile("CVE-"))
        for cve in cves:
            id = cve.getText()
            self.cve+=[id]
            cve_date = re.sub("CVE-","",id)
            cve_date = re.sub("-[0-9\s]*","",cve_date)
            cve_date += "-01-01"
            self.cve_date += [cve_date]
            cve_link = cve.get('href')
            self.cve_link += [cve_link]
            cve_date_publi = self.parser_cve_date_publi(cve)
            self.cve_date_publi += [cve_date_publi]
            #text = cve.parent.previous_sibling.getText()
            #self.cve_text += [text]


    def cvss_parser(self):
        """
        Récupère les vecteur CVSS, les split dans des listes ; récupère aussi les scores CVSS

        Remplie les listes initialisées au préalable (voir fonction __init__ ci-dessus)
        """
        cvsss = self.soup.findAll('a', text=re.compile("AV:"))
        for cvss in cvsss:
            id = cvss.getText()
            id = re.sub("[()]*","",id)
            id = id.split('/')
            self.cvss += [id]
            score = cvss.parent.getText()
            score = re.sub("[A-Za-z0-9\-.,;\s]* score of ","",score)
            score = re.sub(" has[A-Za-z0-9\-.,;\s\(\):/]*","",score)
            self.score += [score]


    def cwe_parser(self):
        """
        Récupère les références CWE, leurs lien, abstraction et structures répertoriées et leurs arborescences SFP1 et SFP2

        Remplie les listes initialisées au préalable (voir fonction __init__ ci-dessus)
        """
        cwes = self.soup.findAll('a', text=re.compile("CWE-"))
        for cwe in cwes:
            id = cwe.getText()
            id = re.sub("[A-Za-z0-9;,:\s\-\(\)\"\']* CWE-","CWE-",id)
            # Lien possiblement cassé
            try:
                pageCWE = opener.open(cwe.get('href'))
            except(urllib.error.URLError) as e:
                continue

            soupCWE = BeautifulSoup(pageCWE, 'html.parser')
            self.cwe += [id]

            # Si l'id désigne une classe de CWE :
            if soupCWE.find('h2', text=re.compile('CWE-')) == None:
                cwe_link = cwe.get('href')
                self.cwe_link += [cwe_link]
                self.abstraction += ["None"]
                self.structure += ["class"]
                self.sfp2 += ["None"]
                self.sfp1 += ["None"]

            # Si l'id désigne un CWE classique :
            else:
                cwe_link = cwe.get('href')
                self.cwe_link += [cwe_link]

                abstruct=soupCWE.find("div",text=re.compile('Weakness')).next_sibling.getText()
                abs = re.sub("Abstraction: ","",abstruct)
                abs = re.sub("Structure: [A-Za-z:\s]*","",abs)
                abs = re.sub(" ", "", abs)
                struct = re.sub("[A-Za-z:\s]*: ","",abstruct)
                self.abstraction += [abs]
                self.structure += [struct]

                sfp2 = soupCWE.find("a",text=re.compile('SFP Secondary'))

                # Possible absence de SFP2 :
                if sfp2 != None:
                    addr = re.sub("/data[A-Za-z0-9/\-:.\s]*",sfp2.get('href'),cwe.get('href'))
                    pageSFP1 = opener.open(addr)
                    soupSFP1 = BeautifulSoup(pageSFP1, 'html.parser')
                    sfp2 = sfp2.getText()
                    sfp2 = re.sub("[A-Z-a-z\s]*: ","",sfp2)
                    self.sfp2 += [sfp2]


                    sfp1 = soupSFP1.find('a', text=re.compile('SFP Primary'))
                    sfp1 = sfp1.getText()
                    sfp1 = re.sub('[A-Za-z\s]*: ','',sfp1)
                    self.sfp1 += [sfp1]
                else:
                    self.sfp2 += ["None"]
                    self.sfp1 += ["None"]
