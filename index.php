<?php
/**
 * AI Video Generator
 * 
 * This script handles user input to generate AI-based videos using OpenAI, Pexels,
 * FFmpeg, and optionally uploads the video to YouTube.
 * 
 * @version 1.1
 */

// Display errors for debugging (disable in production)
ini_set('display_errors', 1);
error_reporting(E_ALL);

// ----------------------------
// Configuration
// ----------------------------

// **API Keys and Credentials**
$OPENAI_API_KEY = getenv('OPENAI_API_KEY');
$PEXELS_API_KEY = getenv('PEXELS_API_KEY');
$YOUTUBE_CLIENT_SECRETS_FILE = 'path_to_your_youtube_credentials.json'; // Path to YouTube OAuth credentials

// **Directories**
$BACKGROUND_VIDEO_FOLDER = 'background_videos/';
$OUTPUT_FOLDER = 'output_videos/';
$AI_IMAGES_FOLDER = 'ai_generated_images/';
$AI_VIDEOS_FOLDER = 'ai_generated_videos/';
$UPLOADS_FOLDER = 'static/uploads/';

// **Ensure Directories Exist**
$directories = [
    $BACKGROUND_VIDEO_FOLDER,
    $OUTPUT_FOLDER,
    $AI_IMAGES_FOLDER,
    $AI_VIDEOS_FOLDER,
    $UPLOADS_FOLDER
];
foreach ($directories as $dir) {
    if (!file_exists($dir)) {
        mkdir($dir, 0777, true);
    }
}

// **FFmpeg Path**
$FFMPEG_PATH = '/usr/bin/ffmpeg'; // Update this path if FFmpeg is installed elsewhere

// ----------------------------
// Helper Functions
// ----------------------------

/**
 * Sanitizes filenames by replacing invalid characters with underscores.
 */
function sanitize_filename($name) {
    return preg_replace('/[^a-zA-Z0-9_\-]/', '_', $name);
}

/**
 * Generates text content using OpenAI's ChatCompletion API.
 */
function generate_text_content($prompt, $length = 150, $OPENAI_API_KEY) {
    $ch = curl_init();

    $data = [
        'model' => 'gpt-3.5-turbo',
        'messages' => [
            ['role' => 'user', 'content' => $prompt]
        ]
    ];

    curl_setopt($ch, CURLOPT_URL, 'https://api.openai.com/v1/chat/completions');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $OPENAI_API_KEY
    ]);

    $response = curl_exec($ch);
    if (curl_errno($ch)) {
        error_log('OpenAI API error: ' . curl_error($ch));
        curl_close($ch);
        return "Default script content due to an error.";
    }
    curl_close($ch);

    $response_data = json_decode($response, true);
    if (isset($response_data['choices'][0]['message']['content'])) {
        return trim($response_data['choices'][0]['message']['content']);
    } else {
        error_log("No valid choices found in the OpenAI response.");
        return "Default script content due to an error.";
    }
}

/**
 * Generates AI images using OpenAI's Image API.
 */
function generate_ai_images($topic, $num_images = 10, $OPENAI_API_KEY, $AI_IMAGES_FOLDER) {
    $images = [];

    for ($i = 0; $i < $num_images; $i++) {
        $prompt = "Create an aesthetically pleasing and detailed image related to {$topic}.";
        $ch = curl_init();

        $data = [
            'prompt' => $prompt,
            'n' => 1,
            'size' => '512x512'
        ];

        curl_setopt($ch, CURLOPT_URL, 'https://api.openai.com/v1/images/generations');
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'Authorization: Bearer ' . $OPENAI_API_KEY
        ]);

        $response = curl_exec($ch);
        if (curl_errno($ch)) {
            error_log("OpenAI Image API error: " . curl_error($ch));
            curl_close($ch);
            continue;
        }
        curl_close($ch);

        $response_data = json_decode($response, true);
        if (isset($response_data['data'][0]['url'])) {
            $image_url = $response_data['data'][0]['url'];
            $image_path = $AI_IMAGES_FOLDER . sanitize_filename("{$topic}_image_{$i}") . ".png";

            // Download the image
            $image_data = file_get_contents($image_url);
            if ($image_data === FALSE) {
                error_log("Failed to download image from URL: {$image_url}");
                continue;
            }

            file_put_contents($image_path, $image_data);
            $images[] = $image_path;
            error_log("Generated image " . ($i + 1) . " for topic '{$topic}'.");
        } else {
            error_log("No URL found in OpenAI Image API response.");
        }
    }

    return $images;
}

/**
 * Fetches Pexels videos related to the topic.
 */
function fetch_pexels_videos($topic, $max_clips = 3, $PEXELS_API_KEY, $UPLOADS_FOLDER) {
    $ch = curl_init();

    curl_setopt($ch, CURLOPT_URL, 'https://api.pexels.com/videos/search?query=' . urlencode($topic) . '&orientation=landscape&per_page=' . $max_clips);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: ' . $PEXELS_API_KEY,
        'User-Agent: Mozilla/5.0'
    ]);

    $response = curl_exec($ch);
    if (curl_errno($ch)) {
        error_log("Pexels API error: " . curl_error($ch));
        curl_close($ch);
        return [];
    }
    curl_close($ch);

    $response_data = json_decode($response, true);
    if (!isset($response_data['videos']) || count($response_data['videos']) == 0) {
        error_log("No videos found for topic '{$topic}'.");
        return [];
    }

    $downloaded_paths = [];
    foreach ($response_data['videos'] as $i => $video) {
        if ($i >= $max_clips) break;
        if (!isset($video['video_files']) || count($video['video_files']) == 0) continue;

        // Select the first video file (you can implement logic to select based on quality)
        $file_link = $video['video_files'][0]['link'];
        $local_path = $UPLOADS_FOLDER . sanitize_filename("{$topic}_clip_{$i}") . ".mp4";

        // Download the video
        $video_data = file_get_contents($file_link);
        if ($video_data === FALSE) {
            error_log("Failed to download video from URL: {$file_link}");
            continue;
        }

        file_put_contents($local_path, $video_data);
        $downloaded_paths[] = $local_path;
        error_log("Downloaded clip " . ($i + 1) . " to: {$local_path}");
    }

    return $downloaded_paths;
}

/**
 * Creates a video from images and adds subtitles.
 */
function create_video_from_images($images, $output_path, $FFMPEG_PATH, $subtitles) {
    // Create a temporary file list for FFmpeg
    $file_list_path = 'file_list.txt';
    $fp = fopen($file_list_path, 'w');
    foreach ($images as $img) {
        fwrite($fp, "file '" . realpath($img) . "'\n");
        fwrite($fp, "duration 5\n"); // Each image displayed for 5 seconds
    }
    fclose($fp);

    // Create slideshow video without audio
    $slideshow_path = 'slideshow.mp4';
    $cmd = "{$FFMPEG_PATH} -y -f concat -safe 0 -i {$file_list_path} -vsync vfr -pix_fmt yuv420p {$slideshow_path}";
    exec($cmd, $output, $return_var);
    if ($return_var !== 0) {
        error_log("Error creating slideshow video.");
        unlink($file_list_path);
        return false;
    }

    // Add subtitles to the slideshow
    $srt_file = 'subtitles.srt';
    $fp = fopen($srt_file, 'w');
    $num_subs = count($subtitles);
    $duration_per_sub = 5; // 5 seconds per subtitle
    for ($i = 0; $i < $num_subs; $i++) {
        $start_time = gmdate("H:i:s", $i * $duration_per_sub) . ",000";
        $end_time = gmdate("H:i:s", ($i + 1) * $duration_per_sub) . ",000";
        fwrite($fp, ($i + 1) . "\n");
        fwrite($fp, "{$start_time} --> {$end_time}\n");
        fwrite($fp, htmlspecialchars($subtitles[$i]) . "\n\n");
    }
    fclose($fp);

    // Overlay subtitles onto the slideshow
    $cmd = "{$FFMPEG_PATH} -y -i {$slideshow_path} -vf subtitles={$srt_file} {$output_path}";
    exec($cmd, $output, $return_var);
    if ($return_var !== 0) {
        error_log("Error adding subtitles to slideshow.");
        unlink($file_list_path);
        unlink($slideshow_path);
        unlink($srt_file);
        return false;
    }

    // Clean up temporary files
    unlink($file_list_path);
    unlink($slideshow_path);
    unlink($srt_file);

    error_log("Final video created at {$output_path}.");
    return true;
}

/**
 * Creates a video from Pexels clips and adds subtitles.
 */
function create_video_from_pexels_clips_with_subtitles($video_paths, $output_path, $FFMPEG_PATH, $subtitles) {
    // Concatenate video clips
    $concat_file = 'concat_list.txt';
    $fp = fopen($concat_file, 'w');
    foreach ($video_paths as $vp) {
        fwrite($fp, "file '" . realpath($vp) . "'\n");
    }
    fclose($fp);

    $concatenated_path = 'concatenated.mp4';
    $cmd = "{$FFMPEG_PATH} -y -f concat -safe 0 -i {$concat_file} -c copy {$concatenated_path}";
    exec($cmd, $output, $return_var);
    if ($return_var !== 0) {
        error_log("Error concatenating video clips.");
        unlink($concat_file);
        return false;
    }

    // Add subtitles (simple SRT generation)
    $srt_file = 'subtitles.srt';
    $fp = fopen($srt_file, 'w');
    $num_subs = count($subtitles);
    $duration_per_sub = 5; // 5 seconds per subtitle
    for ($i = 0; $i < $num_subs; $i++) {
        $start_time = gmdate("H:i:s", $i * $duration_per_sub) . ",000";
        $end_time = gmdate("H:i:s", ($i + 1) * $duration_per_sub) . ",000";
        fwrite($fp, ($i + 1) . "\n");
        fwrite($fp, "{$start_time} --> {$end_time}\n");
        fwrite($fp, htmlspecialchars($subtitles[$i]) . "\n\n");
    }
    fclose($fp);

    // Overlay subtitles onto the concatenated video
    $cmd = "{$FFMPEG_PATH} -y -i {$concatenated_path} -vf subtitles={$srt_file} {$output_path}";
    exec($cmd, $output, $return_var);
    if ($return_var !== 0) {
        error_log("Error adding subtitles to concatenated video.");
        unlink($concat_file);
        unlink($concatenated_path);
        unlink($srt_file);
        return false;
    }

    // Clean up temporary files
    unlink($concat_file);
    unlink($concatenated_path);
    unlink($srt_file);

    error_log("Final video with subtitles created at {$output_path}.");
    return true;
}

/**
 * Uploads video to YouTube using YouTube Data API v3.
 * Note: Implementing OAuth 2.0 flow within a single PHP file is complex.
 * This function assumes you have obtained a valid access token.
 */
function upload_video_to_youtube($video_path, $title, $description, $tags, $YOUTUBE_CLIENT_SECRETS_FILE) {
    // Load Google API PHP Client Library
    require_once 'google-api-php-client/vendor/autoload.php';

    $client = new Google_Client();
    $client->setAuthConfig($YOUTUBE_CLIENT_SECRETS_FILE);
    $client->setScopes(['https://www.googleapis.com/auth/youtube.upload']);
    $client->setAccessType('offline');

    // Token management (simplified)
    $token_path = 'token.json';
    if (file_exists($token_path)) {
        $accessToken = json_decode(file_get_contents($token_path), true);
        $client->setAccessToken($accessToken);
    }

    // Refresh the token if it's expired
    if ($client->isAccessTokenExpired()) {
        if ($client->getRefreshToken()) {
            $client->fetchAccessTokenWithRefreshToken($client->getRefreshToken());
            file_put_contents($token_path, json_encode($client->getAccessToken()));
        } else {
            // Request authorization from the user.
            $authUrl = $client->createAuthUrl();
            echo "Open the following link in your browser to authorize the application:\n$authUrl\n";
            echo "Enter the authorization code: ";
            $authCode = trim(fgets(STDIN));

            // Exchange authorization code for an access token.
            $accessToken = $client->fetchAccessTokenWithAuthCode($authCode);
            $client->setAccessToken($accessToken);

            // Check to see if there was an error.
            if (array_key_exists('error', $accessToken)) {
                throw new Exception(join(', ', $accessToken));
            }

            // Save the token to a file.
            if (!file_exists(dirname($token_path))) {
                mkdir(dirname($token_path), 0700, true);
            }
            file_put_contents($token_path, json_encode($client->getAccessToken()));
        }
    }

    $youtube = new Google_Service_YouTube($client);

    $snippet = new Google_Service_YouTube_VideoSnippet();
    $snippet->setTitle($title);
    $snippet->setDescription($description);
    $snippet->setTags($tags);
    $snippet->setCategoryId("22"); // People & Blogs

    $status = new Google_Service_YouTube_VideoStatus();
    $status->setPrivacyStatus("public"); // or "private", "unlisted"

    $video = new Google_Service_YouTube_Video();
    $video->setSnippet($snippet);
    $video->setStatus($status);

    $chunkSizeBytes = 1 * 1024 * 1024;

    // Setting defer to true tells the client to return a request which can be called
    // with ->execute() instead of making the API call immediately.
    $client->setDefer(true);

    $insertRequest = $youtube->videos->insert("status,snippet", $video);

    // Upload the video in chunks.
    $media = new Google_Http_MediaFileUpload(
        $client,
        $insertRequest,
        'video/*',
        null,
        true,
        $chunkSizeBytes
    );
    $media->setFileSize(filesize($video_path));

    // Read the media file and upload it chunk by chunk.
    $status = false;
    $handle = fopen($video_path, "rb");
    while (!$status && !feof($handle)) {
        $chunk = fread($handle, $chunkSizeBytes);
        $status = $media->nextChunk($chunk);
    }

    fclose($handle);

    // If you want to make other calls after the upload, set setDefer back to false
    $client->setDefer(false);

    return $status->getId();
}

// ----------------------------
// Main Processing Logic
// ----------------------------

$available_langs = [
    'en-US' => 'English (US)',
    'en-GB' => 'English (UK)',
    'es-ES' => 'Spanish',
    'fr-FR' => 'French',
    // Add more languages as needed
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Retrieve form inputs
    $authenticate_choice = $_POST['authenticate'] ?? 'no';
    $content_type = $_POST['content_type'] ?? 'video';
    $topic = sanitize_filename($_POST['topic'] ?? 'default_topic');
    $ai_option = $_POST['ai_option'] ?? 'images';
    $youtube_choice = $_POST['youtube_upload'] ?? 'no';

    // Initialize variables
    $error = '';
    $script = '';
    $video_path = '';
    $uploaded_link = '';

    // Authenticate with YouTube if chosen
    if ($authenticate_choice === 'yes') {
        // Note: Implementing OAuth 2.0 flow within a single PHP file for web is complex.
        // This script provides a simplified version. For a robust solution, separate the OAuth flow.
        // For now, we'll skip YouTube upload if authentication is chosen.
        $error = "YouTube authentication flow is not implemented in this script.";
    }

    if (empty($error)) {
        // Set script length
        $length = ($content_type === 'video') ? 150 : 50;

        // Generate script
        $prompt = "Create a {$length}-word YouTube script about {$topic}.";
        $script = generate_text_content($prompt, $length, $OPENAI_API_KEY);
        $subtitles = explode(". ", $script); // Simple split by period and space

        // Decide the final video file path
        $video_file = $UPLOADS_FOLDER . "{$topic}.mp4";

        if ($ai_option === "images") {
            // Generate AI images
            $images = generate_ai_images($topic, 10, $OPENAI_API_KEY, $AI_IMAGES_FOLDER);
            if (empty($images)) {
                $error = "Failed to generate AI images.";
            } else {
                // Create video from images with subtitles
                $video_creation_success = create_video_from_images($images, $video_file, $FFMPEG_PATH, $subtitles);
                if (!$video_creation_success) {
                    $error = "Failed to create video from images.";
                }
            }
        } elseif ($ai_option === "videos") {
            // Fetch Pexels videos
            $video_clips = fetch_pexels_videos($topic, 3, $PEXELS_API_KEY, $UPLOADS_FOLDER);
            if (empty($video_clips)) {
                $error = "Failed to fetch Pexels videos.";
            } else {
                // Create video from Pexels clips with subtitles
                $video_creation_success = create_video_from_pexels_clips_with_subtitles($video_clips, $video_file, $FFMPEG_PATH, $subtitles);
                if (!$video_creation_success) {
                    $error = "Failed to create video from Pexels clips.";
                }
            }
        } else {
            $error = "Invalid AI option selected.";
        }

        if (empty($error)) {
            // Optionally upload to YouTube
            if ($youtube_choice === 'yes') {
                // Since OAuth 2.0 flow is not implemented, we'll skip uploading
                // You can implement the OAuth flow separately and obtain an access token
                $error = "YouTube upload is not implemented in this script.";
            }

            // If everything succeeded
            if (empty($error)) {
                $video_path = $video_file;
            }
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>AI Video Generator</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 5px; }
        h1 { text-align: center; color: #333; }
        label { display: block; margin-top: 15px; }
        input[type="text"], select { width: 100%; padding: 10px; margin-top: 5px; border-radius: 3px; border: 1px solid #ccc; }
        button { margin-top: 20px; padding: 15px; width: 100%; background: #28a745; color: #fff; border: none; border-radius: 5px; font-size: 16px; }
        .error { color: red; text-align: center; margin-top: 10px; }
        .success { color: green; text-align: center; margin-top: 10px; }
        .result { margin-top: 20px; }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Video Generator</h1>
        
        <?php if ($_SERVER['REQUEST_METHOD'] === 'POST'): ?>
            <?php if (!empty($error)): ?>
                <p class="error"><?php echo htmlspecialchars($error); ?></p>
            <?php else: ?>
                <div class="success">
                    <p>Video generated successfully!</p>
                </div>
                <div class="result">
                    <h2>Script:</h2>
                    <p><?php echo nl2br(htmlspecialchars($script)); ?></p>
                    
                    <h2>Video:</h2>
                    <p><a href="<?php echo htmlspecialchars($video_path); ?>" target="_blank">Download Video</a></p>
                    
                    <?php if (!empty($uploaded_link)): ?>
                        <h2>Uploaded to YouTube:</h2>
                        <p><a href="<?php echo htmlspecialchars($uploaded_link); ?>" target="_blank"><?php echo htmlspecialchars($uploaded_link); ?></a></p>
                    <?php endif; ?>
                </div>
                <a href="index.php">Generate Another Video</a>
            <?php endif; ?>
        <?php endif; ?>

        <form method="POST" enctype="multipart/form-data">
            <label for="authenticate">Authenticate YouTube:</label>
            <select name="authenticate" id="authenticate" required>
                <option value="no" selected>No</option>
                <option value="yes">Yes</option>
            </select>

            <label for="content_type">Content Type:</label>
            <select name="content_type" id="content_type" required>
                <option value="video" selected>Video</option>
                <option value="short">Short</option>
            </select>

            <label for="topic">Topic:</label>
            <input type="text" name="topic" id="topic" required placeholder="Enter topic">

            <label for="ai_option">AI Option:</label>
            <select name="ai_option" id="ai_option" required>
                <option value="images" selected>Images</option>
                <option value="videos">Videos</option>
            </select>

            <label for="youtube_upload">Upload to YouTube:</label>
            <select name="youtube_upload" id="youtube_upload" required>
                <option value="no" selected>No</option>
                <option value="yes">Yes</option>
            </select>

            <button type="submit">Generate Video</button>
        </form>
    </div>
</body>
</html>
