"""Adds support for new data types to sacc."""

from importlib import reload

from astropy.table import Table

import sacc
from sacc.utils import Namespace
from sacc.tracers import BaseTracer

sacc.data_types.required_tags["cluster_counts"] = []
sacc.data_types.required_tags["cluster_mean_log_mass"] = []
sacc.data_types.required_tags["cluster_shear"] = []

sacc.data_types.standard_types = Namespace(*sacc.data_types.required_tags.keys())


class BinZTracer(BaseTracer, tracer_type="bin_z"):  # type: ignore
    """A tracer for a single redshift bin."""

    def __init__(self, name: str, lower: float, upper: float, **kwargs):
        """
        Create a tracer corresponding to a single redshift bin.

        :param name: The name of the tracer
        :param lower: The lower bound of the redshift bin
        :param upper: The upper bound of the redshift bin
        """
        super().__init__(name, **kwargs)
        self.lower = lower
        self.upper = upper

    def __eq__(self, other) -> bool:
        """Test for equality.  If :python:`other` is not a
        :python:`BinZTracer`, then it is not equal to :python:`self`.
        Otherwise, they are equal if names, and the z-range of the bins,
        are equal."""
        if not isinstance(other, BinZTracer):
            return False
        return (
            self.name == other.name
            and self.lower == other.lower
            and self.upper == other.upper
        )

    @classmethod
    def to_tables(cls, instance_list):
        """Convert a list of BinZTracers to a single astropy table

        This is used when saving data to a file.
        One table is generated with the information for all the tracers.

        :param instance_list: List of tracer instances
        :return: List with a single astropy table
        """

        names = ["name", "quantity", "lower", "upper"]

        cols = [
            [obj.name for obj in instance_list],
            [obj.quantity for obj in instance_list],
            [obj.lower for obj in instance_list],
            [obj.upper for obj in instance_list],
        ]

        table = Table(data=cols, names=names)
        table.meta["SACCTYPE"] = "tracer"
        table.meta["SACCCLSS"] = cls.tracer_type
        table.meta["EXTNAME"] = f"tracer:{cls.tracer_type}"
        return [table]

    @classmethod
    def from_tables(cls, table_list):
        """Convert an astropy table into a dictionary of tracers

        This is used when loading data from a file.
        One tracer object is created for each "row" in each table.

        :param table_list: List of astropy tables
        :return: Dictionary of tracers
        """
        tracers = {}

        for table in table_list:
            for row in table:
                name = row["name"]
                quantity = row["quantity"]
                lower = row["lower"]
                upper = row["upper"]
                tracers[name] = cls(name, quantity=quantity, lower=lower, upper=upper)
        return tracers


class BinLogMTracer(BaseTracer, tracer_type="bin_logM"):  # type: ignore
    """A tracer for a single log-mass bin."""

    def __init__(self, name: str, lower: float, upper: float, **kwargs):
        """
        Create a tracer corresponding to a single log-mass bin.

        :param name: The name of the tracer
        :param lower: The lower bound of the log-mass bin
        :param upper: The upper bound of the log-mass bin
        """
        super().__init__(name, **kwargs)
        self.lower = lower
        self.upper = upper

    def __eq__(self, other) -> bool:
        """Test for equality.  If :python:`other` is not a
        :python:`BinLogMTracer`, then it is not equal to :python:`self`.
        Otherwise, they are equal if names, and the z-range of the bins,
        are equal."""
        if not isinstance(other, BinLogMTracer):
            return False
        return (
            self.name == other.name
            and self.lower == other.lower
            and self.upper == other.upper
        )

    @classmethod
    def to_tables(cls, instance_list):
        """Convert a list of BinLogMTracers to a single astropy table

        This is used when saving data to a file.
        One table is generated with the information for all the tracers.

        :param instance_list: List of tracer instances
        :return: List with a single astropy table
        """

        names = ["name", "quantity", "lower", "upper"]

        cols = [
            [obj.name for obj in instance_list],
            [obj.quantity for obj in instance_list],
            [obj.lower for obj in instance_list],
            [obj.upper for obj in instance_list],
        ]

        table = Table(data=cols, names=names)
        table.meta["SACCTYPE"] = "tracer"
        table.meta["SACCCLSS"] = cls.tracer_type
        table.meta["EXTNAME"] = f"tracer:{cls.tracer_type}"
        return [table]

    @classmethod
    def from_tables(cls, table_list):
        """Convert an astropy table into a dictionary of tracers

        This is used when loading data from a file.
        One tracer object is created for each "row" in each table.

        :param table_list: List of astropy tables
        :return: Dictionary of tracers
        """
        tracers = {}

        for table in table_list:
            for row in table:
                name = row["name"]
                quantity = row["quantity"]
                lower = row["lower"]
                upper = row["upper"]
                tracers[name] = cls(name, quantity=quantity, lower=lower, upper=upper)
        return tracers


class BinRichnessTracer(BaseTracer, tracer_type="bin_richness"):  # type: ignore
    """A tracer for a single richness bin."""

    def __eq__(self, other) -> bool:
        """Test for equality. If :python:`other` is not a
        :python:`BinRichnessTracer`, then it is not equal to :python:`self`.
        Otherwise, they are equal if names and the richness-range of the
        bins, are equal."""
        if not isinstance(other, BinRichnessTracer):
            return False
        return (
            self.name == other.name
            and self.lower == other.lower
            and self.upper == other.upper
        )

    def __init__(self, name: str, lower: float, upper: float, **kwargs):
        """
        Create a tracer corresponding to a single richness bin.

        :param name: The name of the tracer
        :param lower: The lower bound of the richness bin
        :param upper: The upper bound of the richness bin
        """
        super().__init__(name, **kwargs)
        self.lower = lower
        self.upper = upper

    @classmethod
    def to_tables(cls, instance_list):
        """Convert a list of BinZTracers to a list of astropy tables

        This is used when saving data to a file.
        One table is generated with the information for all the tracers.

        :param instance_list: List of tracer instances
        :return: List with a single astropy table
        """
        names = ["name", "quantity", "lower", "upper"]

        cols = [
            [obj.name for obj in instance_list],
            [obj.quantity for obj in instance_list],
            [obj.lower for obj in instance_list],
            [obj.upper for obj in instance_list],
        ]

        table = Table(data=cols, names=names)
        table.meta["SACCTYPE"] = "tracer"
        table.meta["SACCCLSS"] = cls.tracer_type
        table.meta["EXTNAME"] = f"tracer:{cls.tracer_type}"
        return [table]

    @classmethod
    def from_tables(cls, table_list):
        """Convert an astropy table into a dictionary of tracers

        This is used when loading data from a file.
        One tracer object is created for each "row" in each table.

        :param table_list: List of astropy tables
        :return: Dictionary of tracers
        """
        tracers = {}

        for table in table_list:
            for row in table:
                name = row["name"]
                quantity = row["quantity"]
                lower = row["lower"]
                upper = row["upper"]
                tracers[name] = cls(
                    name,
                    quantity=quantity,
                    lower=lower,
                    upper=upper,
                )
        return tracers


class BinRadiusTracer(BaseTracer, tracer_type="bin_radius"):  # type: ignore
    """A tracer for a single radial bin."""

    def __eq__(self, other) -> bool:
        """Test for equality. If :python:`other` is not a
        :python:`BinRadiusTracer`, then it is not equal to :python:`self`.
        Otherwise, they are equal if names and the r-range and centers of the
        bins, are equal."""
        if not isinstance(other, BinRadiusTracer):
            return False
        return (
            self.name == other.name
            and self.lower == other.lower
            and self.center == other.center
            and self.upper == other.upper
        )

    def __init__(self, name: str, lower: float, upper: float, center: float, **kwargs):
        """
        Create a tracer corresponding to a single radial bin.

        :param name: The name of the tracer
        :param lower: The lower bound of the radius bin
        :param upper: The upper bound of the radius bin
        :param center: The value to use if a single point-estimate is needed.

        Note that :python:`center` need not be the midpoint between
        :python:`lower` and :python:`upper`'.
        """
        super().__init__(name, **kwargs)
        self.lower = lower
        self.upper = upper
        self.center = center

    @classmethod
    def to_tables(cls, instance_list):
        """Convert a list of BinRadiusTracers to a single astropy table

        This is used when saving data to a file.
        One table is generated with the information for all the tracers.

        :param instance_list: List of tracer instances
        :return: List with a single astropy table
        """

        names = ["name", "quantity", "lower", "upper", "center"]

        cols = [
            [obj.name for obj in instance_list],
            [obj.quantity for obj in instance_list],
            [obj.lower for obj in instance_list],
            [obj.upper for obj in instance_list],
            [obj.center for obj in instance_list],
        ]

        table = Table(data=cols, names=names)
        table.meta["SACCTYPE"] = "tracer"
        table.meta["SACCCLSS"] = cls.tracer_type
        table.meta["EXTNAME"] = f"tracer:{cls.tracer_type}"
        return [table]

    @classmethod
    def from_tables(cls, table_list):
        """Convert an astropy table into a dictionary of tracers

        This is used when loading data from a file.
        One tracer object is created for each "row" in each table.

        :param table_list: List of astropy tables
        :return: Dictionary of tracers
        """
        tracers = {}

        for table in table_list:
            for row in table:
                name = row["name"]
                quantity = row["quantity"]
                lower = row["lower"]
                upper = row["upper"]
                center = row["center"]
                tracers[name] = cls(
                    name,
                    quantity=quantity,
                    lower=lower,
                    upper=upper,
                    center=center,
                )
        return tracers


class ClusterSurveyTracer(BaseTracer, tracer_type="cluster_survey"):  # type: ignore
    """A tracer for the survey definition."""

    def __eq__(self, other) -> bool:
        """Test for equality. If :python:`other` is not a
        :python:`ClusterSurveyTracer`, then it is not equal to :python:`self`.
        Otherwise, they are equal if names and the sky-areas are equal."""
        if not isinstance(other, ClusterSurveyTracer):
            return False
        return self.name == other.name and self.sky_area == other.sky_area

    def __init__(self, name: str, sky_area: float, **kwargs):
        """
        Create a tracer corresponding to the survey definition.

        :param name: The name of the tracer
        :param sky_area: The survey's sky area in square degrees
        """
        super().__init__(name, **kwargs)
        self.sky_area = sky_area

    @classmethod
    def to_tables(cls, instance_list):
        """Convert a list of ClusterSurveyTracer to a list of astropy tables

        This is used when saving data to a file.
        One table is generated with the information for all the tracers.

        :param instance_list: List of tracer instances
        :return: List of astropy tables with one table
        """
        names = ["name", "quantity", "sky_area"]

        cols = [
            [obj.name for obj in instance_list],
            [obj.quantity for obj in instance_list],
            [obj.sky_area for obj in instance_list],
        ]

        table = Table(data=cols, names=names)
        table.meta["SACCTYPE"] = "tracer"
        table.meta["SACCCLSS"] = cls.tracer_type
        table.meta["EXTNAME"] = f"tracer:{cls.tracer_type}"
        return [table]

    @classmethod
    def from_tables(cls, table_list):
        """Convert an astropy table into a dictionary of tracers

        This is used when loading data from a file.
        One tracer object is created for each "row" in each table.

        :param table_list: List of astropy tables
        :return: Dictionary of tracers
        """
        tracers = {}

        for table in table_list:
            for row in table:
                name = row["name"]
                quantity = row["quantity"]
                sky_area = row["sky_area"]
                tracers[name] = cls(
                    name,
                    quantity=quantity,
                    sky_area=sky_area,
                )
        return tracers


reload(sacc)
