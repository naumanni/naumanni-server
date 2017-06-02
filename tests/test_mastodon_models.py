# -*- coding: utf-8 -*-
from naumanni.mastodon_models import Status


def test_status_plain_content():
    # test 1
    status = Status(
        content='''\
<p>インタビュー記事で小隊関連の情報がちらっと出てたため急ぎで育てマン <a href="https://ffxiv-mastodon.com/media/jZSfD2uTTUhbBrydEeg\
"><span class="invisible">https://</span><span class="ellipsis">ffxiv-mastodon.com/media/jZSfD</span><span class="invis\
ible">2uTTUhbBrydEeg</span></a></p>\
    ''',
        media_attachments=[],
    )

    assert status.plainContent == \
        'インタビュー記事で小隊関連の情報がちらっと出てたため急ぎで育てマン https://ffxiv-mastodon.com/media/jZSfD2uTTUhbBrydEeg'
    assert status.urls == ['https://ffxiv-mastodon.com/media/jZSfD2uTTUhbBrydEeg']

    # status with media_attachments
    status = Status(
        content='''\
<p>もうこれも走ってないという事実 <a href="https://friends.nico/media/R9N89nWWqcPSrWU9iL4" rel="nofollow noopener" target="_\
blank"><span class="invisible">https://</span><span class="ellipsis">friends.nico/media/R9N89nWWqcP</span><span class="\
invisible">SrWU9iL4</span></a></p>''',
        media_attachments=[
            {
                'id': 775892, 'remote_url': '', 'type': 'image',
                'url': 'https://d2zoeobnny43zx.cloudfront.net/media_attachments/files/000/775/892/original/2b0a3755a2f583be.jpg',  # noqa
                'preview_url': 'https://d2zoeobnny43zx.cloudfront.net/media_attachments/files/000/775/892/small/2b0a3755a2f583be.jpg',  # noqa
                'text_url': 'https://friends.nico/media/R9N89nWWqcPSrWU9iL4',
                'meta': {
                    'original': {'width': 1280, 'height': 720, 'size': '1280x720', 'aspect': 1.777777777777778},
                    'small': {'width': 400, 'height': 225, 'size': '400x225', 'aspect': 1.777777777777778}
                }
            }
        ]
    )

    assert status.plainContent == \
        'もうこれも走ってないという事実 https://friends.nico/media/R9N89nWWqcPSrWU9iL4'
    assert status.urls == ['https://friends.nico/media/R9N89nWWqcPSrWU9iL4']
    assert status.urls_without_media == []
