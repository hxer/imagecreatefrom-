<?php
$pngfile = 'test4.png';
$newpngfile = 'new4.png';
$im = imagecreatefrompng($pngfile);
imagepng($im,$newpngfile);
?>
