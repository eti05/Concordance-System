-- Extra indexes that help Oracle find data faster.


-- Index on WordID to speed up searches by word.
CREATE INDEX idx_occ_word
ON Occurrences(WordID);


-- Index on DocID to speed up searches by document.
CREATE INDEX idx_occ_doc
ON Occurrences(DocID);


-- Index on WordID and DocID to speed up searches for a word in a document.
CREATE INDEX idx_occ_word_doc
ON Occurrences(WordID, DocID);


-- Index on WordID to speed up connections between words and groups.
CREATE INDEX idx_gm_word
ON GroupMembers(WordID);


-- Index on WordID to speed up connections between words and phrases.
CREATE INDEX idx_pw_word
ON PhraseWords(WordID);


-- Index that helps access the words of a document line in the correct order.
CREATE INDEX idx_occ_doc_line
ON Occurrences(DocID, LineNum, WordPosition);