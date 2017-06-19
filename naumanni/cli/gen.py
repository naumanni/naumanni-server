# -*- coding: utf-8 -*-
import logging

import click

import sys


@click.group('gen')
def cli_gen():
    """`naumanni gen`の起点."""


@cli_gen.command('js')
@click.pass_context
def gen_js(ctx):
    """pluginのnaumanniフロントエンド用エントリポイントを生成する"""
    app = ctx.obj
    out = sys.stdout

    def _l(ln):
        out.write(ln + '\n')

    js_plugins = []
    for plugin in app.plugins.values():
        js_package_name = plugin.js_package_name
        if not js_package_name:
            continue

        kwds = {
            'plugin_id': plugin.id,
            'module': js_package_name,
        }
        js_plugins.append(kwds)

    # export default
    _l('export default {')
    for kwds in js_plugins:
        _l("""\t'{plugin_id}': reqruire('{module}'),""".format(**kwds))
    _l('}')

    # export function loadPluginDefaultLocales()
    _l('export function loadPluginDefaultLocales() {')
    _l('\treturn [')
    for kwds in js_plugins:
        _l("""\t\trequire(/* webpackChunkName: 'locales/[request]' */ '{module}/locales/en'),""".format(**kwds))
    _l('\t]')
    _l('}')

    # export function loadPluginDefaultLocales()
    _l('export function loadPluginLocales(locale) {')
    _l('\treturn [')
    for kwds in js_plugins:
        _l(
            """\t\timport(/* webpackChunkName: 'locales/[request]' */ `{module}/locales/${{locale}}`),"""
            .format(**kwds)
        )
    _l('\t]')
    _l('}')


'''
export default {
  'ogp': require('naumanni-ogp'),
  'spamfilter': require('naumanni-spamfilter'),
}


export function loadPluginDefaultLocales() {
  return [
    require(/* webpackChunkName: 'locales/[request]' */ 'naumanni-ogp/locales/en'),
    require(/* webpackChunkName: 'locales/[request]' */ 'naumanni-spamfilter/locales/en'),
  ]
}


export function loadPluginLocales(locale) {
  return [
    import(/* webpackChunkName: 'locales/[request]' */ `naumanni-ogp/locales/${locale}`),
    import(/* webpackChunkName: 'locales/[request]' */ `naumanni-spamfilter/locales/${locale}`),
  ]
}
'''


@cli_gen.command('css')
@click.pass_context
def gen_css(ctx):
    """pluginのnaumanniフロントエンド用CSSエントリポイントを生成する"""
    app = ctx.obj
    out = sys.stdout

    def _l(ln):
        out.write(ln + '\n')

    plugin_csss = []
    for plugin in app.plugins.values():
        css_file_path = plugin.css_file_path
        if not css_file_path:
            continue

        kwds = {
            'css_path': css_file_path,
        }
        plugin_csss.append(kwds)

    for kwds in plugin_csss:
        _l('@import "{css_path}"'.format(**kwds))
