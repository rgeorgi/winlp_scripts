### `Grant_letters`

```
grant_letters.py -s <spreadsheet> -t <letter_template> -c <config_file> -w <worksheet_num>
```

#### Spreadsheet

The script expects that an excel spreadsheet has been generated with all of the grant recipients names, emails, and other information, with the following columns (zero-indexed):

[0] - response id
[1] - full name of author
[2] - award amount in $USD
[15] - author email address
[18] - author paper title (may be empty)
[19] - Has an email already been sent? (may be empty)

#### Grant Letter Template

The script assumes that you have a worksheet grant letter (.docx) with the following variable fields somewhere in the document:

- `{date}`
  - Date the letter is being generated on
- `{name}`
  - Recipient's name
- `{amount}`
  - Floating point # in USD
- `{text_amount}`
  - Amount of USD written out
- `{paper_title}`
  - Title of the attendee's paper, if they are presnting one.

#### Config

The script also expects a yaml configuration file (default `config.yml`) that specifies a gmail account and password (this may need to be app-specific if you use Oauth or 2-factor auth), as well as a cc address, to include your other co-chairs.

Gmail does not support spoofing a different "From:" address other than the account sending the emails.