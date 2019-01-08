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
#my $all = $prism->basedir->sibling('all.xml');
my $latest = $prism->basedir->sibling('latest.xml');

#$all->spew_raw( generate( $prism->config->{'database'}->{'sql'}->{'all'}, @tags ) );
$latest->spew_raw( generate( $prism->config->{'database'}->{'sql'}->{'latest'}, @tags ) );

sub generate
{
    my ( $sql, @tagnames ) = @_;
    
    my $doc = XML::LibXML::Document->new('1.0', 'utf-8');
    my $root = $doc->createElement("urlset");
    
    # set the date
    my $now = strftime "%Y-%m-%d %H:%M:%S", localtime;
    $root->setAttribute('generated', $now );

    my $sth = $dbh->prepare( $sql )
                       or die "prepare statement failed: $dbh->errstr()";
   $sth->execute();
   
   my ( $node, $sub ) = ();
   
   # loop through each row of the result set, and print it
   # [0] - id, [1] - lang, [2] - title, [3] - abstract, [4] - url, [5] - parent_category, [6] - category, [7] - sub_category, [8] - year, [9] - date
   while( my @data = $sth->fetchrow() )
   {
       my $recall = $doc->createElement( 'recall' );
       # --------------------- #
       # url -> loc
       $node = $doc->createElement( 'url' );
    
       $sub = $doc->createElement( 'loc' );
       $sub->appendText( $data[4] );
       $node->appendChild( $sub );
       # url -> lastmod
       $sub = $doc->createElement( 'lastmod' );
       $sub->appendText( strftime "%Y-%m-%d",localtime( $data[9] ) );
       $node->appendChild( $sub );
       # add to recall
       $recall->appendChild( $node );
       # --------------------- #
       # id
       $node = $doc->createElement( 'id' );
       $node->appendText( sha256_hex( $data[4] ) );
       $recall->appendChild( $node );
       # lang
       $node = $doc->createElement( 'lang' );
       $node->appendText( $data[1] );
       $recall->appendChild( $node );
       # title
       $node = $doc->createElement( 'title' );
       $node->appendChild( XML::LibXML::CDATASection->new( $data[2] ) );
       $recall->appendChild( $node );
       # abstract
       $node = $doc->createElement( 'abstract' );
       $node->appendChild( XML::LibXML::CDATASection->new( $data[3] ) );
       $recall->appendChild( $node );
       # parent
       $node = $doc->createElement( 'parent_category' );
       $node->appendText( $data[5]  );
       $recall->appendChild( $node );
       # category
       $node = $doc->createElement( 'category' );
       $node->appendText( $data[6] );
       $recall->appendChild( $node );
       # subcategory
       $node = $doc->createElement( 'sub_category' );
       $node->appendText( $data[7] );
       $recall->appendChild( $node );
       # year
       $node = $doc->createElement( 'year' );
       $node->appendText( $data[8] );
       $recall->appendChild( $node );

       $root->appendChild( $recall );
   }
   $sth->finish();
   
   $doc->setDocumentElement($root);
   
   return $doc->toString();
   
}
