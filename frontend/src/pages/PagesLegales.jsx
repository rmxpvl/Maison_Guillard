import { Link } from 'react-router-dom'
import { apiGet } from '../api/client.js'
import { CGV_VERSION, MISE_A_JOUR, TEXTE_A_VALIDER } from '../config/legal.js'
import { useApi } from '../hooks/useApi.js'
import { valeurOuACompleter } from '../utils/legal.js'

// What the artisane has not filled in yet is shown highlighted, so nobody publishes it by mistake.
function Champ({ valeur }) {
  const { texte, manquant } = valeurOuACompleter(valeur)
  return manquant ? <mark className="a-completer">{texte}</mark> : <>{texte}</>
}

function useInfos() {
  return useApi(() => apiGet('/informations-legales'), [])
}

function PageLegale({ titre, sousTitre, children }) {
  return (
    <section className="contenu section page-legale">
      <p className="surtitre">Informations</p>
      <h1>{titre}</h1>
      {sousTitre && <p className="page-legale__version">{sousTitre}</p>}
      {TEXTE_A_VALIDER && (
        <p className="a-valider" role="note">
          <strong>Texte modèle, à faire valider par un professionnel avant la mise en ligne.</strong>{' '}
          Les mentions surlignées sont à compléter.
        </p>
      )}
      {children}
    </section>
  )
}

function Identite({ infos }) {
  return (
    <p>
      <strong><Champ valeur={infos.nom_legal} /></strong>, exerçant sous le nom commercial{' '}
      <Champ valeur={infos.nom_commercial} />, SIRET <Champ valeur={infos.siret} />, dont l’atelier est situé{' '}
      <Champ valeur={infos.adresse} />. Contact : <Champ valeur={infos.email} />
      {infos.telephone && <>, <Champ valeur={infos.telephone} /></>}.
    </p>
  )
}

export function PageCgv() {
  const { data: infos } = useInfos()
  const i = infos ?? {}
  return (
    <PageLegale titre="Conditions générales de vente" sousTitre={`Version ${CGV_VERSION}, ${MISE_A_JOUR}`}>
      <h2>1. Qui vend</h2>
      <Identite infos={i} />

      <h2>2. Des pièces fabriquées à la commande</h2>
      <p>
        Toutes les pièces sont fabriquées à la main, à la commande, par l’atelier. Il n’y a pas de stock : le
        prix indiqué sur le site (« à partir de ») est indicatif. Le bois, la céramique ou le papier ont des
        variations naturelles de couleur, de veinage ou de texture : les photos et les finitions présentées
        donnent une idée du rendu, sans l’engager au détail près.
      </p>

      <h2>3. La demande et le devis</h2>
      <p>
        Envoyer une demande ne vous engage pas, et n’engage pas l’atelier. L’atelier vous envoie un devis qui
        fixe le prix final de chaque pièce, les frais de livraison et la date jusqu’à laquelle il est valable.
        Les prix sont en euros. <Champ valeur={i.mention_tva} /> Passé la date de validité, le devis ne peut
        plus être accepté : vous pouvez en demander un nouveau.
      </p>

      <h2>4. Acceptation et paiement</h2>
      <p>
        Vous acceptez le devis en cochant la case « J’accepte les conditions générales de vente » puis en
        cliquant sur « Accepter et payer ». La date, l’heure et la version des présentes conditions sont
        enregistrées. Le paiement se fait en totalité, en ligne, par carte bancaire, sur la page sécurisée de
        notre prestataire Stripe : le site ne voit ni ne conserve votre numéro de carte. La commande est ferme
        à réception du paiement.
      </p>

      <h2>5. Fabrication et livraison</h2>
      <p>
        La fabrication et la livraison sont garanties sous 15 jours après le paiement, sauf cas extrême (par
        exemple un événement indépendant de l’atelier qui empêche de fabriquer ou de livrer). Vous en êtes alors
        informé sans attendre. La livraison se fait à l’adresse indiquée dans votre demande. Vérifiez l’état du
        colis à sa réception et signalez toute réserve au transporteur.
      </p>

      <h2>6. Annuler une commande</h2>
      <ul>
        <li>Avant le paiement : vous pouvez refuser le devis, ou le laisser expirer. Cela ne vous coûte rien.</li>
        <li>
          Après le paiement et tant que la fabrication n’a pas commencé : vous pouvez annuler en ligne depuis la
          page de votre devis et êtes remboursé en totalité, sur le moyen de paiement utilisé (le délai dépend de
          votre banque).
        </li>
        <li>
          Une fois la fabrication commencée : contactez l’atelier. La pièce étant faite pour vous, il décide de
          la suite au cas par cas.
        </li>
      </ul>

      <h2>7. Droit de rétractation</h2>
      <p>
        Les pièces étant confectionnées selon vos spécifications ou nettement personnalisées, le droit de
        rétractation de 14 jours ne s’applique pas (article L221-28 du Code de la consommation).
      </p>

      <h2>8. Garanties légales</h2>
      <p>
        L’atelier reste tenu de la garantie légale de conformité et de la garantie des vices cachés, dans les
        conditions prévues par le Code de la consommation et le Code civil. En cas de problème, écrivez-nous
        d’abord : nous cherchons toujours une solution amiable.
      </p>

      <h2>9. Données personnelles</h2>
      <p>
        Les données que vous nous confiez servent à traiter votre demande et votre commande. Voir la page{' '}
        <Link to="/confidentialite">Données personnelles</Link>.
      </p>

      <h2>10. Médiation et droit applicable</h2>
      <p>
        Conformément à l’article L612-1 du Code de la consommation, vous pouvez recourir gratuitement à un
        médiateur de la consommation : <mark className="a-completer">à compléter (nom et coordonnées du médiateur)</mark>.
        Les présentes conditions sont soumises au droit français.
      </p>
    </PageLegale>
  )
}

export function PageMentionsLegales() {
  const { data: infos } = useInfos()
  const i = infos ?? {}
  return (
    <PageLegale titre="Mentions légales" sousTitre={`Mise à jour : ${MISE_A_JOUR}`}>
      <h2>Éditeur du site</h2>
      <Identite infos={i} />
      <p>Directeur de la publication : <mark className="a-completer">à compléter</mark>.</p>

      <h2>Hébergement</h2>
      <p>
        Le site et ses données sont hébergés par Render Services, Inc. (render.com), dans un centre de données
        situé à Francfort (Allemagne). Les photos des produits sont hébergées par Cloudinary (cloudinary.com).
      </p>

      <h2>Prestataires techniques</h2>
      <ul>
        <li>Paiement par carte : Stripe Payments Europe, Ltd. (stripe.com).</li>
        <li>Envoi des e-mails : Brevo (brevo.com).</li>
      </ul>

      <h2>Propriété intellectuelle</h2>
      <p>
        Les photos, les textes et les créations présentés sur ce site appartiennent à l’atelier. Toute
        reproduction sans son accord écrit est interdite.
      </p>

      <h2>Données personnelles</h2>
      <p>Voir la page <Link to="/confidentialite">Données personnelles</Link>.</p>
    </PageLegale>
  )
}

export function PageConfidentialite() {
  const { data: infos } = useInfos()
  const i = infos ?? {}
  return (
    <PageLegale titre="Données personnelles" sousTitre={`Mise à jour : ${MISE_A_JOUR}`}>
      <h2>Qui est responsable de vos données</h2>
      <Identite infos={i} />

      <h2>Ce que nous collectons, et pourquoi</h2>
      <ul>
        <li>
          <strong>Votre demande</strong> : nom, e-mail, téléphone (facultatif), adresse de livraison, pièces
          demandées et messages. Pour répondre, établir votre devis, fabriquer et livrer votre commande.
        </li>
        <li>
          <strong>Votre compte</strong> (facultatif) : votre e-mail et un mot de passe, que nous ne conservons
          jamais en clair. Pour retrouver vos demandes et échanger avec l’atelier.
        </li>
        <li>
          <strong>Votre paiement</strong> : le montant et l’identifiant du paiement. Votre numéro de carte est
          saisi chez Stripe et ne passe jamais par ce site.
        </li>
      </ul>

      <h2>Combien de temps</h2>
      <p>
        Les demandes sans suite sont conservées au plus 3 ans après le dernier échange. Les commandes et leurs
        justificatifs de paiement le sont 10 ans, comme l’exige la loi comptable. Votre compte est conservé tant
        que vous ne le supprimez pas.
      </p>

      <h2>Vos droits</h2>
      <p>
        Vous pouvez accéder à vos données, les faire corriger, les faire effacer, vous opposer à leur
        utilisation, en demander la limitation ou la portabilité. Vous pouvez supprimer votre compte vous-même
        depuis « Mon compte » : vos demandes passées restent alors chez l’atelier, sans lien avec un compte,
        pour ses obligations comptables. Pour toute autre demande, écrivez à <Champ valeur={i.email} />. Vous
        pouvez aussi vous plaindre auprès de la CNIL (cnil.fr).
      </p>

      <h2>Qui reçoit vos données</h2>
      <ul>
        <li>Render (hébergement du site, en Allemagne) ;</li>
        <li>Stripe (paiement par carte) ;</li>
        <li>Brevo (envoi des e-mails : devis, confirmations, messages) ;</li>
        <li>Cloudinary (photos des produits : aucune donnée de client).</li>
      </ul>
      <p>
        Certains de ces prestataires peuvent traiter des données hors de l’Union européenne, avec les garanties
        prévues par le règlement européen (clauses contractuelles types).
      </p>

      <h2>Cookies et stockage dans votre navigateur</h2>
      <p>
        Ce site n’utilise ni cookie de mesure d’audience ni cookie publicitaire : il n’y a donc pas de bandeau
        à accepter. Votre navigateur garde seulement, pour le fonctionnement du site, votre demande en cours et,
        si vous avez un compte, votre connexion.
      </p>

      <h2>Sécurité</h2>
      <p>
        Les échanges sont chiffrés (HTTPS), les mots de passe sont protégés par un hachage, le nombre de
        tentatives de connexion est limité et l’accès à la gestion du site est réservé à l’atelier.
      </p>
    </PageLegale>
  )
}
