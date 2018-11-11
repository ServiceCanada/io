#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;

use Prism;
use DBI;
use YAML::Tiny;
use XML::LibXML;

use POSIX qw(strftime tzset);
use Digest::SHA qw(sha256_hex);

# =================
# = PREPROCESSING =
# =================
# Lets set the correct timezone
$ENV{'TZ'} = 'America/Toronto';

my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1 }
);

my @tags = @{ $prism->config->{'xml'}->{'tags'} };

# Write to file
my $all = $prism->basedir->sibling('all.xml');
my $latest = $prism->basedir->sibling('latest.xml');

# $all->spew_raw( generate( $prism->config->{'database'}->{'sql'}->{'all'}, @tags ) );
$latest->spew_raw( generate( $prism->config->{'database'}->{'sql'}->{'latest'}, @tags ) );

sub generate
{
    my ( $sql, @tagnames ) = @_;
    
    my $doc = XML::LibXML::Document->new('1.0', 'utf-8');
    my $root = $doc->createElement("recalls");
    
    # set the date
    my $now = strftime "%Y-%m-%d %H:%M:%S", localtime;
    $root->setAttribute('generated', $now );

    my $sth = $dbh->prepare( $sql )
                       or die "prepare statement failed: $dbh->errstr()";
   $sth->execute();
   
   # loop through each row of the result set, and print it
   while( my @data = $sth->fetchrow() )
   {
       my $recall = $doc->createElement( 'recall' );
       for ( my $idx = 0; $idx < scalar( @tagnames ); $idx++ )
       {
               my $tag = $doc->createElement( $tagnames[$idx] );
               $tag->appendTextNode( ( $tagnames[$idx] eq 'id' ) ? sha256_hex( $data[4] ) : $data[$idx] );
               $recall->appendChild( $tag );
       }
       $root->appendChild( $recall );
   }
   $sth->finish();
   
   $doc->setDocumentElement($root);
   
   return $doc->toString();
   
}
