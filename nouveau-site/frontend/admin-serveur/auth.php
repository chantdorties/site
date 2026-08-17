<?php
/**
 * Première étape du relais d’authentification de l’administration.
 *
 * Decap ouvre cette page dans une fenêtre surgissante. Elle ne fait que rediriger vers
 * GitHub en emportant un jeton anti-rejeu : le secret, lui, n’est utilisé qu’à l’étape
 * suivante, dans callback.php.
 *
 * Le fichier de secrets est volontairement hors du dossier publié.
 */

declare(strict_types=1);

require __DIR__ . '/../orties-admin-secret.php';
$reglages = reglages_relais();

if (($_SERVER['HTTPS'] ?? '') !== 'on' && ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') !== 'https') {
    http_response_code(400);
    exit('Le relais exige HTTPS.');
}

// GitHub refuse les portées qu’il ne connaît pas ; on n’accepte que celles dont
// l’administration a besoin, plutôt que de recopier le paramètre reçu.
$portees = ['repo', 'public_repo'];
$portee = in_array($_GET['scope'] ?? '', $portees, true) ? $_GET['scope'] : 'repo';

$jeton = bin2hex(random_bytes(16));
setcookie('relais_etat', $jeton, [
    'expires' => time() + 600,
    'path' => '/',
    'secure' => true,
    'httponly' => true,
    'samesite' => 'Lax',
]);

$destination = 'https://github.com/login/oauth/authorize?' . http_build_query([
    'client_id' => $reglages['client_id'],
    'redirect_uri' => $reglages['origine'] . '/callback.php',
    'scope' => $portee,
    'state' => $jeton,
]);

header('Location: ' . $destination, true, 302);
