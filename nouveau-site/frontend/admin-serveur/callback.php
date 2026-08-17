<?php
/**
 * Seconde étape du relais : GitHub renvoie ici un code à usage unique, qu’il faut
 * échanger contre un jeton en présentant le secret. C’est la seule raison d’être de ce
 * relais : un navigateur ne peut pas détenir ce secret.
 *
 * Le jeton est ensuite remis à Decap par « postMessage », suivant le protocole qu’il
 * attend : la fenêtre surgissante annonce sa présence, l’administration répond, la
 * fenêtre transmet alors la charge utile. L’origine est toujours nommée explicitement —
 * avec « * », n’importe quelle page ouvrant ce relais repartirait avec un jeton
 * autorisant l’écriture dans le dépôt.
 */

declare(strict_types=1);

require __DIR__ . '/../orties-admin-secret.php';
$reglages = reglages_relais();

if (($_SERVER['HTTPS'] ?? '') !== 'on' && ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') !== 'https') {
    http_response_code(400);
    exit('Le relais exige HTTPS.');
}

/**
 * Rend la page qui parle à Decap, puis s’arrête.
 *
 * Le script est un fichier à part, jamais écrit ici : la politique de sécurité du
 * sous-domaine impose « script-src 'self' », et un script inline serait refusé par le
 * navigateur — la fenêtre resterait alors sur « Connexion en cours… », quel que soit le
 * résultat de l’échange. Le message voyage donc par des attributs « data- ».
 */
function repondre_a_decap(string $type, string $charge, string $origine): never
{
    $message = 'authorization:github:' . $type . ':' . $charge;
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store');
    $message_html = htmlspecialchars($message, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $origine_html = htmlspecialchars($origine, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    echo <<<HTML
    <!doctype html>
    <html lang="fr"><head><meta charset="utf-8"><title>Connexion</title></head>
    <body><p id="etat">Connexion en cours…</p>
    <script src="callback.js" data-origine="{$origine_html}" data-message="{$message_html}"></script>
    </body></html>
    HTML;
    exit;
}

$origine = $reglages['origine'];

$attendu = $_COOKIE['relais_etat'] ?? '';
$recu = $_GET['state'] ?? '';
setcookie('relais_etat', '', ['expires' => time() - 3600, 'path' => '/', 'secure' => true, 'httponly' => true]);

if ($attendu === '' || $recu === '' || !hash_equals($attendu, $recu)) {
    repondre_a_decap('error', json_encode(['message' => 'Jeton anti-rejeu invalide'], JSON_THROW_ON_ERROR), $origine);
}

$code = $_GET['code'] ?? '';
if ($code === '') {
    repondre_a_decap('error', json_encode(['message' => 'Code d’autorisation absent'], JSON_THROW_ON_ERROR), $origine);
}

$requete = curl_init('https://github.com/login/oauth/access_token');
curl_setopt_array($requete, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 15,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ['Accept: application/json'],
    CURLOPT_USERAGENT => 'relais-chantdorties',
    CURLOPT_POSTFIELDS => http_build_query([
        'client_id' => $reglages['client_id'],
        'client_secret' => $reglages['client_secret'],
        'code' => $code,
        'redirect_uri' => $origine . '/callback.php',
    ]),
]);
$reponse = curl_exec($requete);
$erreur = curl_error($requete);
curl_close($requete);

if ($reponse === false) {
    repondre_a_decap('error', json_encode(['message' => 'GitHub injoignable : ' . $erreur], JSON_THROW_ON_ERROR), $origine);
}

$donnees = json_decode((string) $reponse, true);
if (!is_array($donnees) || empty($donnees['access_token'])) {
    $motif = is_array($donnees) ? ($donnees['error_description'] ?? $donnees['error'] ?? 'réponse inattendue') : 'réponse illisible';
    repondre_a_decap('error', json_encode(['message' => 'Échange refusé : ' . $motif], JSON_THROW_ON_ERROR), $origine);
}

repondre_a_decap('success', json_encode([
    'token' => $donnees['access_token'],
    'provider' => 'github',
], JSON_THROW_ON_ERROR), $origine);
