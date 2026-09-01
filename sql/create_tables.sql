-- Concordance System database schema.
-- Creates the 8 tables used by the project.


-- Stores the authors.
CREATE TABLE Authors (
  AuthorID   NUMBER GENERATED ALWAYS AS IDENTITY,
  AuthorName VARCHAR2(200) NOT NULL,

  CONSTRAINT pk_authors PRIMARY KEY (AuthorID),
  CONSTRAINT uq_authors_name UNIQUE (AuthorName)
);


-- Stores the documents in the system.
CREATE TABLE Documents (
  DocID    NUMBER GENERATED ALWAYS AS IDENTITY,
  Title    VARCHAR2(300) NOT NULL,
  AuthorID NUMBER NOT NULL,
  PubYear  NUMBER(4),
  Source   VARCHAR2(500),
  LoadDate DATE DEFAULT SYSDATE NOT NULL,

  CONSTRAINT pk_documents PRIMARY KEY (DocID),

  -- Each document has an author.
  CONSTRAINT fk_documents_author
    FOREIGN KEY (AuthorID) REFERENCES Authors(AuthorID),

  -- The same author cannot have two documents with the same title.
  CONSTRAINT uq_documents_title UNIQUE (Title, AuthorID),

  -- Checks that the year is valid.
  CONSTRAINT ck_documents_year
    CHECK (PubYear IS NULL OR PubYear BETWEEN 0 AND 2100)
);


-- Stores the words found in the documents.
CREATE TABLE Words (
  WordID   NUMBER GENERATED ALWAYS AS IDENTITY,
  WordText VARCHAR2(100) NOT NULL,

  CONSTRAINT pk_words PRIMARY KEY (WordID),
  CONSTRAINT uq_words_text UNIQUE (WordText)
);


-- Stores every place where a word appears.
CREATE TABLE Occurrences (
  OccID        NUMBER GENERATED ALWAYS AS IDENTITY,
  DocID        NUMBER NOT NULL,
  WordID       NUMBER NOT NULL,
  ParagraphNum NUMBER NOT NULL,
  LineNum      NUMBER NOT NULL,
  WordPosition NUMBER NOT NULL,

  CONSTRAINT pk_occurrences PRIMARY KEY (OccID),

  -- Connects the occurrence to its document and word.
  CONSTRAINT fk_occ_doc
    FOREIGN KEY (DocID) REFERENCES Documents(DocID) ON DELETE CASCADE,

  CONSTRAINT fk_occ_word
    FOREIGN KEY (WordID) REFERENCES Words(WordID),

  -- A position in a document can only contain one occurrence.
  CONSTRAINT uq_occ_position
    UNIQUE (DocID, ParagraphNum, LineNum, WordPosition),

  -- Position numbers must be positive.
  CONSTRAINT ck_occ_pos
    CHECK (ParagraphNum > 0 AND LineNum > 0 AND WordPosition > 0)
);


-- Stores groups of words.
CREATE TABLE Groups (
  GroupID   NUMBER GENERATED ALWAYS AS IDENTITY,
  GroupName VARCHAR2(100) NOT NULL,

  CONSTRAINT pk_groups PRIMARY KEY (GroupID),
  CONSTRAINT uq_groups_name UNIQUE (GroupName)
);


-- Connects words to groups.
CREATE TABLE GroupMembers (
  GroupID NUMBER NOT NULL,
  WordID  NUMBER NOT NULL,

  -- A word can appear only once in the same group.
  CONSTRAINT pk_groupmembers PRIMARY KEY (GroupID, WordID),

  CONSTRAINT fk_gm_group
    FOREIGN KEY (GroupID) REFERENCES Groups(GroupID) ON DELETE CASCADE,

  CONSTRAINT fk_gm_word
    FOREIGN KEY (WordID) REFERENCES Words(WordID) ON DELETE CASCADE
);


-- Stores phrases.
CREATE TABLE Phrases (
  PhraseID   NUMBER GENERATED ALWAYS AS IDENTITY,
  PhraseText VARCHAR2(500) NOT NULL,

  CONSTRAINT pk_phrases PRIMARY KEY (PhraseID),
  CONSTRAINT uq_phrases_text UNIQUE (PhraseText)
);


-- Stores the words that make up each phrase.
CREATE TABLE PhraseWords (
  PhraseID NUMBER NOT NULL,
  SeqNum   NUMBER NOT NULL,
  WordID   NUMBER NOT NULL,

  -- SeqNum keeps the order of the words in the phrase.
  CONSTRAINT pk_phrasewords PRIMARY KEY (PhraseID, SeqNum),

  CONSTRAINT fk_pw_phrase
    FOREIGN KEY (PhraseID) REFERENCES Phrases(PhraseID) ON DELETE CASCADE,

  CONSTRAINT fk_pw_word
    FOREIGN KEY (WordID) REFERENCES Words(WordID),

  -- Word position in a phrase starts from 1.
  CONSTRAINT ck_pw_seq CHECK (SeqNum > 0)
);