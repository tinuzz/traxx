{% set x = 0 -%}
[playlist]
{{ "" }}
{%- for r in rows -%}
{% set x = x + 1 -%}
File{{ x }}={{ url_for('serve_file', fileid=r.id, _external=True) }}
Title{{ x }}={{ r.title }}
Length{{ x }}={{ r.length|int }}
{% endfor -%}
NumberOfEntries={{ num }}
