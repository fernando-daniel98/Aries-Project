import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine
from pysus.ftp.databases.sih import SIH
from conectandoBancoDeDados import downloadDadosSIHSUS

# Fazendo o download dos dados SIH/SUS
