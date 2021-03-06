from Advisory import Advisory
from bs4 import BeautifulSoup
import urllib.request
import re


"""
ICS-CERT n'accepte pas les requetes ne venant pas de navigateurs,
on change alors le User-Agent de nos requete pour se faire passer
pour Mozilla Firefox:
"""
class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"

# Crée une instance d'opener d'url avec le bon User-Agent
opener = AppURLopener()





def fill(mdp,i):
    # Récupération du code html de l'url de la première page des advisories de ICS-CERT
    url_ics = "https://ics-cert.us-cert.gov/advisories?page=" + str(i)
    page = opener.open(url_ics)
    soup = BeautifulSoup(page, 'html.parser')

    # Récupère les urls de tous les advisories de la première page
    urls = soup.findAll('a', href=re.compile('/advisories/I'))
    # Récupère et envoie en bdd les données des 10 premiers advisories
    for i in range(len(urls)):
        url = urls[i].get('href')
        url = "https://ics-cert.us-cert.gov"+url
        adv = Advisory(url,mdp)
        adv.send_to_db()
