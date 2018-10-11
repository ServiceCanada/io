#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Prism;
use JSON::MaybeXS;
use Path::Tiny qw/path/;
use SQL::Abstract;
use DBI;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
        'dbi:SQLite:dbname='.$prism->parent( 'public' )->sibling( 'db/news/database.sqlite' )->stringify,
        '', '',
        { RaiseError => 0, AutoCommit => 1, PrintError => 0 }
    );

my ( $cache, $queries )  = ( {}, {
'article' => $dbh->prepare( 'INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?)'),
'department' => $dbh->prepare( 'INSERT OR REPLACE INTO departments VALUES (?, ?, ?)'),
'minister' => $dbh->prepare( 'INSERT OR REPLACE INTO ministers VALUES (?, ?, ?)'),
'type' => $dbh->prepare( 'INSERT OR REPLACE INTO types VALUES (?, ?, ?)'),
'pivot_department' => $dbh->prepare( 'INSERT INTO article_department VALUES (?, ?)'),
'pivot_minister' => $dbh->prepare( 'INSERT INTO article_minister VALUES (?, ?)'),
'pivot_type' => $dbh->prepare( 'INSERT INTO article_type VALUES (?, ?)')
});

while ( my $resource = $prism->next() )
{
    my ( $uri, $saveas, $lang ) =  ( delete $resource->{'uri'}, delete $resource->{'source'}, $resource->{'lang'} );
    
    my $datafile = $prism->download( $uri, $saveas );
    
    next unless $datafile;
    
    my $json = decode_json( $datafile->slurp );
    
    foreach my $record ( @{ $json->{'data'} } )
    {
      
    #lets 
      
      my ( $department, $minister, $type  ) = map { lookup( $_, $lang, delete $record->{ $_ } )  } ( 'DEPT', 'MINISTER', 'TYPE' );
      
      my $record = $prism->transform( $record, $resource );
      
      next if ( seen($record->{'id'}) );

      $queries->{'article'}->execute(  map { $record->{$_} } ('id', 'link', 'pubdate', 'title', 'teaser', 'lang' ) );

      for ( @{ $department } )
      {
          $queries->{'pivot_department'}->execute( $record->{'id'}, $_ ) unless has( 'department', $record->{'id'}, $_ );
      }

      for ( @{ $minister })
      {
          $queries->{'pivot_minister'}->execute( $record->{'id'}, $_ ) unless has( 'minister', $record->{'id'}, $_ );
      }

      for ( @{ $type })
      {
           $queries->{'pivot_type'}->execute( $record->{'id'}, $_ ) unless ( has( 'type', $record->{'id'}, $_ ) );
      }

      say " [indexed] ".$record->{'link'};

    }
}

# ====================
# = HELPER FUNCTIONS =
# ====================


sub lookup
{
    my ( $type, $lang, $data ) = @_;
    
    $type = ( $type eq 'DEPT' ) ? 'department' : lc( $type );

    my ( $id ) = $dbh->selectrow_array( "SELECT id FROM ".$type."s WHERE $lang = '$data' LIMIT 1" );
    
    return  $id;
}

sub seen {
    my ( $id ) = @_;
    return ( $dbh->selectrow_array( "SELECT * FROM articles WHERE id = '$id' LIMIT 1" ) ) ? 1 : 0 ; 
}

sub has
{
    my ( $type, $article, $other ) = @_;
    return ($dbh->selectrow_array( "SELECT * FROM article_$type WHERE article_id = '$article' AND ".$type."_id = '$other' LIMIT 1" ) ) ? 1 : 0; 
}


