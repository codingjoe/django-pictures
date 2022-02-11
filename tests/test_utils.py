import pytest

from pictures import utils


class TestGrid:
    def test_default(self):
        assert list(utils._grid()) == [
            ("xs", 1.0),
            ("s", 1.0),
            ("m", 1.0),
            ("l", 1.0),
            ("xl", 1.0),
        ]

    def test_small_up(self):
        assert list(utils._grid(xs=6)) == [
            ("xs", 0.5),
            ("s", 0.5),
            ("m", 0.5),
            ("l", 0.5),
            ("xl", 0.5),
        ]

    def test_mixed(self):
        assert list(utils._grid(s=6, l=9)) == [
            ("xs", 1.0),
            ("s", 0.5),
            ("m", 0.5),
            ("l", 0.75),
            ("xl", 0.75),
        ]

    def test_key_error(self):
        with pytest.raises(KeyError) as e:
            list(utils._grid(xxxxl=6))
        assert "Invalid breakpoint: xxxxl. Choices are: xs, s, m, l, xl" in str(e.value)


class TestSizes:
    def test_default(self):
        assert utils.sizes() == "100vw"

    def test_default__container(self):
        assert (
            utils.sizes(container_width=1200)
            == "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px"
        )

    def test_bottom_up(self):
        assert utils.sizes(xs=6) == "50vw"

    def test_bottom_up__container(self):
        assert (
            utils.sizes(container_width=1200, xs=6)
            == "(min-width: 0px) and (max-width: 1199px) 50vw, 600px"
        )

    def test_medium_up(self):
        assert utils.sizes(s=6) == "(min-width: 0px) and (max-width: 767px) 100vw, 50vw"

    def test_medium_up__container(self):
        assert (
            utils.sizes(container_width=1200, s=6)
            == "(min-width: 0px) and (max-width: 767px) 100vw,"
            " (min-width: 768px) and (max-width: 1199px) 50vw,"
            " 600px"
        )

    def test_mixed(self):
        assert (
            utils.sizes(s=6, l=9) == "(min-width: 0px) and (max-width: 767px) 100vw,"
            " (min-width: 768px) and (max-width: 1199px) 50vw,"
            " 75vw"
        )

    def test_mixed__container(self):
        assert (
            utils.sizes(container_width=1200, s=6, l=9)
            == "(min-width: 0px) and (max-width: 767px) 100vw,"
            " (min-width: 768px) and (max-width: 1199px) 75vw,"
            " 600px"
        )


class TestSourceSet:
    def test_default(self):
        assert utils.source_set((800, 600), ratio=3 / 2, max_width=1200, cols=12) == {
            800,
            100,
            200,
            300,
            400,
            500,
            600,
            700,
        }

    def test_different_aspect(self):
        assert utils.source_set((800, 600), ratio=1 / 1, max_width=1200, cols=12) == {
            100,
            200,
            300,
            400,
            500,
            600,
        }

    def test_very_large_img(self):
        size = 6000, 4000  # 24MP
        assert utils.source_set(size, ratio=1 / 1, max_width=1200, cols=6) == {
            800,
            1600,
            2400,
            1000,
            200,
            2000,
            400,
            1200,
            600,
        }


def test_placeholder():
    utils.placeholder.cache_clear()
    img = utils.placeholder(1600, 1200, "tiny")
    assert img.width == 1600
    assert img.height == 1200
