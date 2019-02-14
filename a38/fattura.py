from . import models
from . import fields


NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"


class IdFiscale(models.Model):
    id_paese = fields.StringField(length=2)
    id_codice = fields.StringField(max_length=28)


class IdTrasmittente(IdFiscale):
    pass


class IdFiscaleIVA(IdFiscale):
    pass


class ContattiTrasmittente(models.Model):
    telefono = fields.StringField(min_length=5, max_length=12, null=True)
    email = fields.StringField(min_length=7, max_length=256, null=True)


class DatiTrasmissione(models.Model):
    id_trasmittente = IdTrasmittente
    progressivo_invio = fields.ProgressivoInvioField()
    formato_trasmissione = fields.StringField(length=5, choices=("FPR12", "FPA12"))
    codice_destinatario = fields.StringField(null=True, min_length=6, max_length=7)
    contatti_trasmittente = fields.ModelField(ContattiTrasmittente, null=True)
    pec_destinatario = fields.StringField(null=True, min_length=8, max_length=256)

    def validate_model(self):
        super().validate_model()
        if self.codice_destinatario is None and self.pec_destinatario is None:
            self.validation_error(("codice_destinatario", "pec_destinatario"), "one of codice_destinatario or pec_destinatario must be set")


class Anagrafica(models.Model):
    denominazione = fields.StringField(max_length=80, null=True)
    nome = fields.StringField(max_length=60, null=True)
    cognome = fields.StringField(max_length=60, null=True)
    titolo = fields.StringField(min_length=2, max_length=10, null=True)
    cod_eori = fields.StringField(xmltag="CodEORI", min_length=13, max_length=17, null=True)

    def validate_model(self):
        super().validate_model()
        if self.denominazione is None:
            if self.nome is None or self.cognome is None:
                self.validation_error(("nome", "cognome", "denominazione"), "nome and cognome must both be set if denominazione is empty")
        else:
            if self.nome is not None or self.cognome is not None:
                self.validation_error(("nome", "cognome", "denominazione"), "nome and cognome must not be set if denominazione is not empty")


class DatiAnagraficiBase(models.Model):
    id_fiscale_iva = IdFiscaleIVA
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)
    anagrafica = Anagrafica

    def get_xmltag(self):
        return "DatiAnagrafici"


class DatiAnagraficiCedentePrestatore(DatiAnagraficiBase):
    regime_fiscale = fields.StringField(
            length=4, choices=("RF01", "RF02", "RF04", "RF05", "RF06", "RF07",
                               "RF08", "RF09", "RF10", "RF11", "RF12", "RF13",
                               "RF14", "RF15", "RF16", "RF17", "RF18", "RF19"))


class Sede(models.Model):
    indirizzo = fields.StringField(max_length=60)
    numero_civico = fields.StringField(max_length=8, null=True)
    cap = fields.StringField(xmltag="CAP", length=5)
    comune = fields.StringField(max_length=60)
    provincia = fields.StringField(length=2, null=True)
    nazione = fields.StringField(length=2)


class IscrizioneREA(models.Model):
    ufficio = fields.StringField(length=2)
    numero_rea = fields.StringField(xmltag="NumeroREA", max_length=20)
    capitale_sociale = fields.StringField(min_length=4, max_length=15, null=True)
    socio_unico = fields.StringField(length=2, choices=("SU", "SM"), null=True)
    stato_liquidazione = fields.StringField(length=2, choices=("LS", "LN"))


class Contatti(models.Model):
    telefono = fields.StringField(min_length=5, max_length=12, null=True)
    fax = fields.StringField(min_length=5, max_length=12, null=True)
    email = fields.StringField(min_length=7, max_length=256, null=True)


class CedentePrestatore(models.Model):
    dati_anagrafici = DatiAnagraficiCedentePrestatore
    sede = Sede
    # stabile_organizzazione
    iscrizione_rea = fields.ModelField(IscrizioneREA, null=True)
    contatti = fields.ModelField(Contatti, null=True)
    riferimento_amministrazione = fields.StringField(max_length=20, null=True)


class DatiAnagraficiCessionarioCommittente(DatiAnagraficiBase):
    pass


class CessionarioCommittente(models.Model):
    dati_anagrafici = DatiAnagraficiCessionarioCommittente
    sede = Sede
    # stabile_organizzazione
    # rappresentante_fiscale


class FatturaElettronicaHeader(models.Model):
    dati_trasmissione = DatiTrasmissione
    cedente_prestatore = CedentePrestatore
    cessionario_committente = CessionarioCommittente


class DatiGeneraliDocumento(models.Model):
    tipo_documento = fields.StringField(length=4, choices=("TD01", "TD02", "TD03", "TD04", "TD05", "TD06"))
    divisa = fields.StringField()
    data = fields.DateField()
    numero = fields.StringField(max_length=20)
    importo_totale_documento = fields.DecimalField(max_length=15)
    causale = fields.StringField(max_length=200)


class DettaglioLinee(models.Model):
    numero_linea = fields.IntegerField(max_length=4)
    descrizione = fields.StringField(max_length=1000)
    quantita = fields.DecimalField(max_length=21, decimals=2, null=True)
    unita_misura = fields.StringField(max_length=10, null=True)
    prezzo_unitario = fields.DecimalField(max_length=21)
    prezzo_totale = fields.DecimalField(max_length=21)
    aliquota_iva = fields.DecimalField(xmltag="AliquotaIVA", max_length=6)


class DatiRiepilogo(models.Model):
    aliquota_iva = fields.DecimalField(xmltag="AliquotaIVA", max_length=6)
    imponibile_importo = fields.DecimalField(max_length=15)
    imposta = fields.DecimalField(max_length=15)
    esigibilita_iva = fields.StringField(xmltag="EsigibilitaIVA", length=1, choices=("I", "D", "S"), null=True)
    riferimento_normativo = fields.StringField(max_length=100, null=True)


class DatiBeniServizi(models.Model):
    dettaglio_linee = fields.ModelListField(DettaglioLinee)
    dati_riepilogo = fields.ModelListField(DatiRiepilogo)

    def add_dettaglio(self, **kw):
        kw.setdefault("numero_linea", len(self.dettaglio_linee) + 1)
        self.dettaglio_linee.append(DettaglioLinee(**kw))


class DatiGenerali(models.Model):
    dati_generali_documento = DatiGeneraliDocumento


class FatturaElettronicaBody(models.Model):
    dati_generali = DatiGenerali
    dati_beni_servizi = DatiBeniServizi


class Fattura(models.Model):
    fattura_elettronica_header = FatturaElettronicaHeader
    fattura_elettronica_body = FatturaElettronicaBody

    def validate(self):
        self.fattura_elettronica_header.dati_trasmissione.formato_trasmissione = self.get_versione()
        super().validate()

    def get_versione(self):
        return None

    def get_xmltag(self):
        return "FatturaElettronica"

    def get_xmlattrs(self):
        return {"versione": self.get_versione()}

    def to_xml(self, builder):
        with builder.element(self.get_xmltag(), **self.get_xmlattrs()) as b:
            with b.override_default_namespace(None) as b1:
                for name, field in self._meta.items():
                    field.to_xml(b1, getattr(self, name))

    def build_etree(self):
        """
        Build and return an ElementTree with the fattura in XML format
        """
        from a38.builder import Builder
        builder = Builder()
        builder.default_namespace = NS
        self.to_xml(builder)
        return builder.get_tree()


class FatturaPrivati(Fattura):
    def get_versione(self):
        return "FPR12"


class FatturaPA(Fattura):
    def get_versione(self):
        return "FPR12"
