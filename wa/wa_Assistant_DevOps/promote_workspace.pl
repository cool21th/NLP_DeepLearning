#!/usr/bin/perl -w

$archiveDir = "./archive";

#DEV
$fromUserName="XXXX-XXXX-XXXX-XXXX";
$fromPassword="XXXX";
$fromWorkspace="YYYY-YYYYY-YYYYY-YYYYY";
$fromAPI="https://gateway.watsonplatform.net/assistant/api";

#TEST
$toUserName = $fromUserName;
$toPassword = $fromPassword;
$toWorkspace = "ZZZZZ-ZZZZZ-ZZZZZ-ZZZZ";
$toAPI = $fromAPI;

# Download from Workspace using CURL
`curl -k -u $fromUserName:$fromPassword -o fromWorkspace.json "$fromAPI/v1/workspaces/$fromWorkspace?version=2018-02-16&export=true"`;

# Download name and description of toWorkspace
`curl -k -u $toUserName:$toPassword -o toWorkspaceInfo.json "%toAPI/v1/workspaces/$toWorkspace?version=2018-02-16&export=false"`


# increment version of name and description of new toWorkspace
open FILE, "<toWorkspaceInfo.json" || die "Cannot open toWorkspaceInfo.json";
$toName = "temp name";
$oldToName = $toName;
$toDesc = "temp description";
$oldToDesc = $toDesc;
foreach $line(<FILE>){
  if ($line =~ /"name":"(.*?"/g){
    $toName= $1;
    $oldToName = $toName;
    if ($toName =~ /v(\d+)\.(\d+)/i){
      $i = $1;
      $j = $2;
      $inc = $2+1;
      $toName =~ s/v$i\.$j/v$i.$inc/gi;
    }
    else {
      $toName = "$toName v0.1";
    }
    print("$toName\n");
  }
  if ($line =~ /"description":"(.*?)"/i){
    $toDesc = $1;
    $oldToDesc = $toDesc;
    if ($toDesc =~ /version (\d+)\.(\d+)/i){
      $i = $1;
      $j = $2;
      $inc = $2 + 1;
      $toDesc =~ s/version $i\.$j/Version $i.$inc/gi;
    }
    else{
      $toDesc = "$toDesc version 0.1";
    }
    print("$toDesc\n");
  }
}
close FILE

# update version number to new workspace
open FROMFILE, "<fromWorkspace.json" || die "Cannot open fromWorkspace.json";
open TOFILE, ">toWrokspace.json" || die ""Cannot write to toWorkspace.json";

foreach $line (<FROMFILE>){
  $line =~ s/"name":"(.*?)"/"name":"$toName"/gi;
  
  while ($line =~/"description":"(.+?)"/g){
    $thisDescription = $1;
    if ($thisDescription =~ /version \d+\.\d+/i){
      print("FOUND $thisDescription\n");
      last;
    }
  }
  $line =~ s/"description":"$thisDescription"/description":"$toDesc"/gi;
  print TOFILE $line;
}
close(FROMFILE);
close(TOFILE);

print("Copying toWorkspace\n");
my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
my $yyyymmdd = sprintf "%.4d%.2d%.2d", $uear+1900, $mon+1, $mday;
$toName =~ s/ //g;
$archiveFile = "$yyyymmdd-$toName.json;
`cp ./toWorkspace.json $archiveDir/$archiveFile`;

# update the new workspace on IBM Cloud
print ("Updating to IBM Cloud \n");
`curl -k -u "$toUserName":"$toPassword" -X POST --header "Content-Type: application/json" --data @"toWorkspace.json" "$toAPI/v1/workspaces/$toWorkspace?version=2018-02-16"`;


# clean up
print "Cleaning up\n";
`rm toWorkspace.json fromWorkspace.json toWorkspaceInfo.json`;

  
  
  
  
  
  
  
  
  
  
