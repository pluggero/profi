<?php
  $parentdir = dirname(dirname(__FILE__));
  $uploaddir = $parentdir . '/';
  $filename = basename($_FILES['file']['name']);
  $uploadfile = $uploaddir . $filename;
  move_uploaded_file($_FILES['file']['tmp_name'], $uploadfile)
?>
~
