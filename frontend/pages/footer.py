from __future__ import annotations

import streamlit as st


FOOTER_HTML = (
    "<div class='footer-bar'>Nordicamo is part of the research project "
    "<a href='https://ruc.dk/en/forskningsprojekt/alternative-media-and-ideological-counterpublics' "
    "target='_blank' rel='noopener'>AlterPublics</a> based at "
    "<a href='https://ruc.dk/en' target='_blank' rel='noopener'>Roskilde University</a> (Denmark) and "
    "supported by the <a href='https://digitalmedialab.ruc.dk/' target='_blank' rel='noopener'>"
    "Digital Media Lab</a> (RUC) (thanks!).</div>"
)


def render_footer_bar() -> None:
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)
