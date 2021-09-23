#!/usr/bin/python

#JAYASINGHA Prashani | RICHOU Jacques | ODIER Raphael

#importation des librairies
import csv
import datetime
import time,sys,os,math,smbus
import RPi.GPIO as GPIO
import Adafruit_DHT

#les numeros des pins connectees sur le rpi(en version BCM) concernant l ADC sont definies en variables globale
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8

#fonction permettant de rajouter les donnees des return des fonction dans un fichier CSV
def ecrire_csv(num,temp,humid,lumin,gaz,son,vibe,heure,minute,seconde,jour,mois,annee):

        #ouverture du fichier CSV
        with open('test.csv', 'a') as csvfile:
                #on definit les delimiteurs et separateurs
                message = csv.writer(csvfile, delimiter=';', quotechar=',', quoting=csv.QUOTE_MINIMAL)
                #on ecrit les donnees dans le fichier CSV
                message.writerow([num,temp,humid,lumin,gaz,son,vibe,heure,minute,seconde,jour,mois,annee])
                #csvfile.close()


#fonction permettant de setup les channels du MCP 3008
def setup():

        GPIO.setwarnings(False)

        #on utilise les numero gpio des ports
        GPIO.setmode(GPIO.BCM)

        # on defini les entrees/sorties pour la com spi
        GPIO.setup(SPIMOSI, GPIO.OUT)
        GPIO.setup(SPIMISO, GPIO.IN)
        GPIO.setup(SPICLK, GPIO.OUT)
        GPIO.setup(SPICS, GPIO.OUT)


#fonction de lecture du mcp
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        #si le nombre concernant le ch a lire n est pas compris entre 0 et 7
        if ((adcnum > 7) or (adcnum < 0)):
                return -1

        GPIO.output(cspin, True)      # CS etat haut
        GPIO.output(clockpin, False)  # start clock etat bas
        GPIO.output(cspin, False)     # CS etat bas

        commandout = adcnum # affecte le numero de chx a cammandout
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # on envoit  bits ici

        #lit l ensemble de la trame recue
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # lit12 bit : un vide , un null , 10 pour les valeurs ADC
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)

        adcout >>= 1       # le premier bit est 'null' on l ignore
        return adcout


#fonction permettant de lire la temperature
def readTemp():

        #a partir de la librairie Adafruit_DHT on obtient la valeur de l humidite
        humidity, temperature = Adafruit_DHT.read_retry(11,4)
        temperature = int(temperature)

        #decommentez ces lignes pour afficher le resultat dans la console
        #print 'Valeur du capteur de temperature sur le pin 7 (bcm4) du raspberry'
        #print 'Temp: {0:0.1f} C'.format(temperature)

        return temperature

#fonction permettant de lire le pourcentage d humidite
def readHum():

        #a partir de la librairie Adafruit_DHT on obtient la valeur de l humidite
        humidity, temperature = Adafruit_DHT.read_retry(11,4)
        humidity = int(humidity)

        #decommentez ces lignes pour afficher le resultat dans la console
        #print 'Valeur du capteur de l humidite sur le pin 7 (bcm4) du raspberry'
        #print 'Humidity: %s pourcent' %humidity

        return humidity

#fonction permettant de calculer le nombre de LUX recu
def readLum():

        #formule du nombre de LUX a partir de la valeur brut :
        #VLum = 3.3*valeur_ADC/1024
        #a partir de la valeur de cette tension on trouve la valeur de la resistance variable
        #RLum = (tensionAlimentation*Rtirage/VLum)-Rtirage
        #on peut ensuite calculer la valeur en Lux
        #LUX = (RLum/(2.84*10^4))^1.40
        #(ce calcul a ete separe en deux parties en dessous)

        #declaration des variables
        tensionAlim = 3.330             #V
        RTirage = 10000.000             #Ohm
        tensionLum = 0.000              #V

        #lecture ADC channel 3
        CH3_ADC = readadc(3,SPICLK,SPIMOSI,SPIMISO,SPICS)

        #conversion de la valeur brute lue en miliVolts
        tensionLum_mV = CH3_ADC*( 3300.0 / 1024.0)

        #conversion en Volt
        tensionLum_V = tensionLum_mV/1000

        #calcul de la resistance variable
        RLum = ((tensionAlim*RTirage)/tensionLum_V)-RTirage

        #Calcul du nombre de LUX (lux_p resultat intermediaire, lux_f resultat final)
        Lux_intermediaire = (RLum)/(2.84*pow(10,4))
        Lux_final = pow(Lux_intermediaire,1.40)

        #decommentez ces lignes pour afficher les resultats des etapes dans la console"
        #print "Valeur en tension du capteur de luminosite sur ch3 : "
        #print "Tension : %s millivolts" %tensionLum_mV
        #print "Tension %s V"  %tensionLum_V
        #print "R photoresistance : %s Ohm" %RLum
        #print "Lux_p : %s" %Lux_p
        #print "Lux_f : %s" %Lux_f

        Lux_str = '{0:0.2f}'.format(Lux_final)
        Lux = float(Lux_str)

        return Lux


#fonction permettant de calculer le nombre de ppm de CO
def readGaz():

        #formule du nombre de ppm a partir de la valeur brut :
        #valeur tension VRL = valeur_ADC*3.3/1024)
        #valeur ppm = 3.027*exp(1.0698*VRL)
        #nous sommes oblige de le faire ligne par ligne car le resultat est de zero sinon

        #lecture ADC sur le channel 1
        CH1_ADC = readadc(1,SPICLK,SPIMOSI,SPIMISO,SPICS)

        #calcul de VRL
        VRL = CH1_ADC*3.3
        VRL = VRL/1024

        #calcul de ppm
        facteur = 1.0698*VRL
        vexpo = math.exp(facteur)
        ppm = 3.027*vexpo

        #decommentez ces lignes si vous voulez afficher dans la console VRL et le nombre de ppm
        #print "VRL = %s" %VRL
        #print "Nombre de particule par metre = %s" %ppm

        ppm_str = '{0:0.2f}'.format(ppm)
        PPM = float(ppm_str)

        return PPM

#fonction permettant de calculer le volume sonore en dB
def readSon():

        #formule du volume sonore a partir de la valeure brut: k*log(valeur_ADC)*log10(e^1)

        k = 10                                                          #facteur k = 10
        CH4_ADC = readadc(4,SPICLK,SPIMOSI,SPIMISO,SPICS)               #lecture de la valeur brut sur le channel 4
        volume_son = k*math.log(CH4_ADC)*math.log10(math.exp(1))        #application de la formule
        #print "Volume sonore : %s dB" % format(volume_son, ".2f")      #decommentez cette ligne pour l'afficher dans la console

        dB_str = '{0:0.2f}'.format(volume_son)
        dB = float(dB_str)

        return dB

#fonction permettant de connaitre la presence de Vibration
def readVib():

        #Dans cette fonction on connait la vibration en fonction de l angle du capteur

        #on lit le port I2C 1 du Rpi 3b+ (soit 0 soit 1)
        bus = smbus.SMBus(1)
        #on definit un buffer a l adresse 0x60
        address = 0x60

        #orientation255 du registre 1
        #orientation255 = bus.read_byte_data(address,1)

        #orientation 3599 du registre 2 et 3
        orien_registre_2 = bus.read_byte_data(address,2)
        orien_registre_3 = bus.read_byte_data(address,3)
        orien  = (orien_registre_2 << 8) + orien_registre_3
        orien  = orien/10.0

        #pour afficher la valeur de l orientation dans la console decommentez cette ligne
        #print "valeur orientation = ",orientation255

        angle = int(orien)

        return(angle)

#fonction retournant l annee
def get_annee():

        year = time.strftime("%Y")
        year = int(year)
        return year


#fonction retournant le mois
def get_mois():

        month = time.strftime("%m")
        month = int(month)
        return(month)


#fonction retournant le jour
def get_jour():

        day = time.strftime("%d")
        day = int(day)
        return(day)


#fonction retournant l heure
def get_heure():

        hour = time.strftime("%H")
        hour = int(hour)
        return(hour)


#fonction retournant la minute
def get_minute():

        min = time.strftime("%M")
        min = int(min)
        return(min)


#fonction retournant les secondes
def get_seconde():

        sec = time.strftime("%S")
        sec = int(sec)
        return(sec)


#fonction main
def main(num):

        #on lit dans cette boucle de ch0 a ch7
        for i in range(0,8):
                analogChannel = i

                if (analogChannel < 0) or (analogChannel > 7):                  #si le numero de la channel n'est pas comprise entre 0 et 7 il  y a une erreur
                        print ('Mauvais numero de chaine ... erreur!')
                        print ('Cela va de 0 a 7...')

                #else:
                        #decommentez cette ligne si vous voulez avoir les valeurs bruts des chaines
                        #on affecte a cette variable ce que retourne la fonction servant a lire les channels
                        #reception_adc  = readadc(analogChannel, SPICLK, SPIMOSI, SPIMISO, SPICS)
                        #print ('Valeur de CH %d du MCP3008 : %d'%(analogChannel,reception_adc))


        temp = readTemp()                                                               #lecture temperature           ( C )
        hum  = readHum()                                                                #lecture humidite              ( % )
        lum  = readLum()                                                                #lecture de la lumiere         (LUX)
        gaz  = readGaz()                                                                #lecture de la quantitee de CO (ppm)
        son  = readSon()                                                                #lecture du volume sonore      ( dB)
        vib  = readVib()                                                                #lecture des vibrations       (Angle)
        heure = get_heure()
        minute = get_minute()
        seconde = get_seconde()
        jour = get_jour()
        mois = get_mois()
        annee = get_annee()

        #ecriture des donnees dans le fichier csv
        ecrire_csv(num,temp,hum,lum,gaz,son,vib,heure,minute,seconde,jour,mois,annee)

        time.sleep(6.5)

#fonction permettant de tout effacer de la memoire une fois le scrpit finit
def destroy():

        GPIO.cleanup()


#Tant que a est vrai le programme va s'executer en boucle sauf si on appuit sur crtl+c
a = True
j = 0

while a == True :

        #si le nom de la fonctio est main
        if __name__ == '__main__':
                #appel de la fonction setup()
                setup()

                try:
                        print "Mesure ", j
                        #appel de la fonction main
                        main(j)
                        j = j+1
                #Quand 'Ctrl+C' est presse le programme s interrompt
                except KeyboardInterrupt:
                        #et on cleanup tout ca
                        destroy()
                        #on sort de notre boucle
                        a = False


