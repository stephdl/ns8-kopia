#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Alert mail texts. Each entry is (subject, body), formatted with str.format()."""

TEMPLATES = {
    "en": {
        "test": ("Kopia test mail from {host}",
                 "This test mail comes from the Kopia backup server {host}.\nAlert mails will reach you the same way."),
        "owner_late": ("Backup late: {machine}",
                       "The machine {machine} has not completed a backup to {host} for {hours} hours.\n"
                       "Last backup: {last}.\n\nPlease switch the machine on, connect it to the network and leave Kopia running."),
        "admin_late": ("Backup late: {machine} ({hours} h)",
                       "The machine {machine} has not completed a backup to {host} for {hours} hours.\n"
                       "Last backup: {last}.\nOwner: {owner}."),
        "back_ok": ("Backup back to normal: {machine}",
                    "The machine {machine} completed a backup to {host} again at {last}."),
        "verify_failed": ("Backup verification failed on {host}",
                          "The periodic check of the backup repository of {host} found errors:\n\n{details}"),
        "never": "never",
    },
    "fr": {
        "test": ("Mail de test Kopia depuis {host}",
                 "Ce mail de test vient du serveur de sauvegarde Kopia {host}.\nLes alertes vous parviendront de la même façon."),
        "owner_late": ("Sauvegarde en retard : {machine}",
                       "La machine {machine} n'a pas terminé de sauvegarde vers {host} depuis {hours} heures.\n"
                       "Dernière sauvegarde : {last}.\n\nAllumez la machine, connectez-la au réseau et laissez Kopia tourner."),
        "admin_late": ("Sauvegarde en retard : {machine} ({hours} h)",
                       "La machine {machine} n'a pas terminé de sauvegarde vers {host} depuis {hours} heures.\n"
                       "Dernière sauvegarde : {last}.\nPropriétaire : {owner}."),
        "back_ok": ("Sauvegarde revenue à la normale : {machine}",
                    "La machine {machine} a de nouveau terminé une sauvegarde vers {host} le {last}."),
        "verify_failed": ("Échec de la vérification des sauvegardes sur {host}",
                          "La vérification périodique du dépôt de sauvegarde de {host} a trouvé des erreurs :\n\n{details}"),
        "never": "jamais",
    },
    "it": {
        "test": ("Mail di prova Kopia da {host}",
                 "Questa mail di prova arriva dal server di backup Kopia {host}.\nGli avvisi ti arriveranno allo stesso modo."),
        "owner_late": ("Backup in ritardo: {machine}",
                       "La macchina {machine} non ha completato un backup verso {host} da {hours} ore.\n"
                       "Ultimo backup: {last}.\n\nAccendi la macchina, collegala alla rete e lascia Kopia in esecuzione."),
        "admin_late": ("Backup in ritardo: {machine} ({hours} h)",
                       "La macchina {machine} non ha completato un backup verso {host} da {hours} ore.\n"
                       "Ultimo backup: {last}.\nProprietario: {owner}."),
        "back_ok": ("Backup tornato normale: {machine}",
                    "La macchina {machine} ha di nuovo completato un backup verso {host} il {last}."),
        "verify_failed": ("Verifica dei backup fallita su {host}",
                          "Il controllo periodico del repository di backup di {host} ha trovato errori:\n\n{details}"),
        "never": "mai",
    },
    "de": {
        "test": ("Kopia-Testmail von {host}",
                 "Diese Testmail kommt vom Kopia-Backupserver {host}.\nWarnungen erreichen Sie auf dem gleichen Weg."),
        "owner_late": ("Sicherung überfällig: {machine}",
                       "Der Rechner {machine} hat seit {hours} Stunden keine Sicherung auf {host} abgeschlossen.\n"
                       "Letzte Sicherung: {last}.\n\nBitte schalten Sie den Rechner ein, verbinden Sie ihn mit dem Netz und lassen Sie Kopia laufen."),
        "admin_late": ("Sicherung überfällig: {machine} ({hours} h)",
                       "Der Rechner {machine} hat seit {hours} Stunden keine Sicherung auf {host} abgeschlossen.\n"
                       "Letzte Sicherung: {last}.\nBesitzer: {owner}."),
        "back_ok": ("Sicherung wieder normal: {machine}",
                    "Der Rechner {machine} hat am {last} wieder eine Sicherung auf {host} abgeschlossen."),
        "verify_failed": ("Prüfung der Sicherungen fehlgeschlagen auf {host}",
                          "Die regelmäßige Prüfung des Sicherungs-Repositorys von {host} hat Fehler gefunden:\n\n{details}"),
        "never": "nie",
    },
    "es": {
        "test": ("Correo de prueba de Kopia desde {host}",
                 "Este correo de prueba viene del servidor de copias Kopia {host}.\nLas alertas le llegarán de la misma forma."),
        "owner_late": ("Copia atrasada: {machine}",
                       "El equipo {machine} no ha completado una copia en {host} desde hace {hours} horas.\n"
                       "Última copia: {last}.\n\nEncienda el equipo, conéctelo a la red y deje Kopia en marcha."),
        "admin_late": ("Copia atrasada: {machine} ({hours} h)",
                       "El equipo {machine} no ha completado una copia en {host} desde hace {hours} horas.\n"
                       "Última copia: {last}.\nPropietario: {owner}."),
        "back_ok": ("Copia de nuevo normal: {machine}",
                    "El equipo {machine} ha completado de nuevo una copia en {host} el {last}."),
        "verify_failed": ("Fallo en la verificación de copias en {host}",
                          "La comprobación periódica del repositorio de copias de {host} encontró errores:\n\n{details}"),
        "never": "nunca",
    },
    "pt": {
        "test": ("Mensagem de teste do Kopia em {host}",
                 "Esta mensagem de teste vem do servidor de cópias Kopia {host}.\nOs alertas chegarão da mesma forma."),
        "owner_late": ("Cópia em atraso: {machine}",
                       "A máquina {machine} não concluiu uma cópia para {host} há {hours} horas.\n"
                       "Última cópia: {last}.\n\nLigue a máquina, ligue-a à rede e deixe o Kopia a correr."),
        "admin_late": ("Cópia em atraso: {machine} ({hours} h)",
                       "A máquina {machine} não concluiu uma cópia para {host} há {hours} horas.\n"
                       "Última cópia: {last}.\nProprietário: {owner}."),
        "back_ok": ("Cópia de novo normal: {machine}",
                    "A máquina {machine} concluiu de novo uma cópia para {host} em {last}."),
        "verify_failed": ("Falha na verificação das cópias em {host}",
                          "A verificação periódica do repositório de cópias de {host} encontrou erros:\n\n{details}"),
        "never": "nunca",
    },
    "pt_BR": {
        "test": ("E-mail de teste do Kopia em {host}",
                 "Este e-mail de teste vem do servidor de backup Kopia {host}.\nOs alertas chegarão do mesmo jeito."),
        "owner_late": ("Backup atrasado: {machine}",
                       "A máquina {machine} não concluiu um backup em {host} há {hours} horas.\n"
                       "Último backup: {last}.\n\nLigue a máquina, conecte-a à rede e deixe o Kopia rodando."),
        "admin_late": ("Backup atrasado: {machine} ({hours} h)",
                       "A máquina {machine} não concluiu um backup em {host} há {hours} horas.\n"
                       "Último backup: {last}.\nProprietário: {owner}."),
        "back_ok": ("Backup normalizado: {machine}",
                    "A máquina {machine} concluiu de novo um backup em {host} em {last}."),
        "verify_failed": ("Falha na verificação dos backups em {host}",
                          "A verificação periódica do repositório de backup de {host} encontrou erros:\n\n{details}"),
        "never": "nunca",
    },
    "eu": {
        "test": ("Kopia proba-mezua {host} zerbitzaritik",
                 "Proba-mezu hau {host} Kopia babeskopia-zerbitzaritik dator.\nAlertak modu berean iritsiko zaizkizu."),
        "owner_late": ("Babeskopia atzeratuta: {machine}",
                       "{machine} makinak ez du babeskopiarik amaitu {host} zerbitzarian azken {hours} orduetan.\n"
                       "Azken babeskopia: {last}.\n\nPiztu makina, konektatu sarera eta utzi Kopia martxan."),
        "admin_late": ("Babeskopia atzeratuta: {machine} ({hours} h)",
                       "{machine} makinak ez du babeskopiarik amaitu {host} zerbitzarian azken {hours} orduetan.\n"
                       "Azken babeskopia: {last}.\nJabea: {owner}."),
        "back_ok": ("Babeskopia normaltasunera itzuli da: {machine}",
                    "{machine} makinak berriro babeskopia bat amaitu du {host} zerbitzarian: {last}."),
        "verify_failed": ("Babeskopien egiaztapenak huts egin du {host} zerbitzarian",
                          "{host} zerbitzariko babeskopia-biltegiaren aldizkako egiaztapenak erroreak aurkitu ditu:\n\n{details}"),
        "never": "inoiz ez",
    },
}


def word(key, lang):
    return TEMPLATES.get(lang, TEMPLATES["en"]).get(key) or TEMPLATES["en"][key]


def render(kind, lang, **values):
    subject, body = TEMPLATES.get(lang, TEMPLATES["en"]).get(kind) or TEMPLATES["en"][kind]
    return subject.format(**values), body.format(**values)
