-- Makes sure all words are saved in the same format.
-- For example: "Love", "love" and "LOVE" are all saved as "love".


CREATE OR REPLACE TRIGGER trg_words_normalize

-- Runs before a word is inserted or updated.
BEFORE INSERT OR UPDATE ON Words
FOR EACH ROW

BEGIN

  -- Removes spaces and changes the word to lower case.
  :NEW.WordText := LOWER(TRIM(:NEW.WordText));

END;
/