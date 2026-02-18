from unittest.mock import patch


class TestCreateLiteratureNoteImpl:
    """Tests for _create_literature_note_impl."""

    def test_required_args_only(self):
        """Should call mdv new literature with title, short_title, and --batch."""
        with patch("mdvault_mcp_server.tools.tasks_projects.run_mdv_command", return_value="OK") as mock_cmd:
            from mdvault_mcp_server.tools.tasks_projects import _create_literature_note_impl

            result = _create_literature_note_impl(
                title="KAN: Kolmogorov-Arnold Networks",
                short_title="kan",
            )

            mock_cmd.assert_called_once_with([
                "new", "literature", "KAN: Kolmogorov-Arnold Networks", "--batch",
                "--var", "short_title=kan",
            ])
            assert result == "OK"

    def test_all_args(self):
        """Should pass all optional args as --var pairs."""
        with patch("mdvault_mcp_server.tools.tasks_projects.run_mdv_command", return_value="OK") as mock_cmd:
            from mdvault_mcp_server.tools.tasks_projects import _create_literature_note_impl

            _create_literature_note_impl(
                title="Attention Is All You Need",
                short_title="attention",
                authors="Vaswani, Shazeer",
                year=2017,
                url="https://arxiv.org/abs/1706.03762",
                source_type="article",
            )

            call_args = mock_cmd.call_args[0][0]
            assert call_args[:4] == ["new", "literature", "Attention Is All You Need", "--batch"]
            assert "short_title=attention" in call_args
            assert "authors=Vaswani, Shazeer" in call_args
            assert "year=2017" in call_args
            assert "url=https://arxiv.org/abs/1706.03762" in call_args
            assert "source_type=article" in call_args

    def test_no_optional_args_omits_vars(self):
        """Should not include optional --var entries when not provided."""
        with patch("mdvault_mcp_server.tools.tasks_projects.run_mdv_command", return_value="OK") as mock_cmd:
            from mdvault_mcp_server.tools.tasks_projects import _create_literature_note_impl

            _create_literature_note_impl(title="Some Paper", short_title="some-paper")

            call_args = mock_cmd.call_args[0][0]
            assert not any("year=" in a for a in call_args)
            assert not any("authors=" in a for a in call_args)
            assert not any("url=" in a for a in call_args)
            assert not any("source_type=" in a for a in call_args)

    def test_extra_vars(self):
        """Should pass extra_vars as --var pairs."""
        with patch("mdvault_mcp_server.tools.tasks_projects.run_mdv_command", return_value="OK") as mock_cmd:
            from mdvault_mcp_server.tools.tasks_projects import _create_literature_note_impl

            _create_literature_note_impl(
                title="A Paper",
                short_title="a-paper",
                extra_vars={"status": "reading"},
            )

            call_args = mock_cmd.call_args[0][0]
            assert "status=reading" in call_args
