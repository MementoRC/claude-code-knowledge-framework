/**
 * Pattern Search Component
 * Comprehensive interface for searching and browsing knowledge patterns
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  CardActions,
  Chip,
  Grid,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Slider,
  Collapse,
  IconButton,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Paper,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterListIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Visibility as VisibilityIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Share as ShareIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';

import { apiService } from '../../services/api';
import {
  PatternSearchRequest,
  PatternSearchResponse,
  Pattern,
  TechStackFilter,
} from '../../types/patterns';

const PATTERN_TYPES = [
  'setup',
  'bugfix',
  'optimization',
  'best_practice',
  'architecture',
];

const COMMON_TECHNOLOGIES = [
  'React',
  'TypeScript',
  'Python',
  'FastAPI',
  'Node.js',
  'Docker',
  'PostgreSQL',
  'Redis',
  'AWS',
  'GCP',
  'JavaScript',
  'Vue.js',
  'Angular',
  'Django',
  'Flask',
  'Express.js',
  'MongoDB',
  'MySQL',
  'Kubernetes',
];

const PROJECT_TYPES = [
  'web_application',
  'api_service',
  'mobile_app',
  'desktop_app',
  'cli_tool',
  'library',
  'microservice',
  'monolith',
];

const COMPLEXITY_LEVELS = ['low', 'medium', 'high'];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`pattern-tabpanel-${index}`}
      aria-labelledby={`pattern-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function PatternSearch() {
  // State management
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<TechStackFilter>({});
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [queryTime, setQueryTime] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [minSimilarity, setMinSimilarity] = useState(0.7);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // Search function
  const searchPatterns = useCallback(async (searchQuery: string, searchFilters: TechStackFilter, pageNumber: number = 1) => {
    if (!searchQuery.trim()) {
      setPatterns([]);
      setTotalCount(0);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: PatternSearchRequest = {
        query: searchQuery,
        filters: searchFilters,
        limit,
        min_similarity: minSimilarity,
      };

      const response: PatternSearchResponse = await apiService.searchPatterns(request);

      setPatterns(response.patterns);
      setTotalCount(response.total_count);
      setQueryTime(response.query_time_ms);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed. Please try again.');
      setPatterns([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [limit, minSimilarity]);

  // Effect for search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query.trim()) {
        searchPatterns(query, filters, page);
      }
    }, 500); // Debounce search

    return () => clearTimeout(timeoutId);
  }, [query, filters, page, searchPatterns]);

  // Handle filter changes
  const handleFilterChange = (field: keyof TechStackFilter, value: any) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
    setPage(1); // Reset to first page when filters change
  };

  // Handle pattern detail view
  const handlePatternDetail = (pattern: Pattern) => {
    setSelectedPattern(pattern);
    setDetailDialogOpen(true);
  };

  // Pattern card component
  const PatternCard = ({ pattern }: { pattern: Pattern }) => (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" gutterBottom>
          {pattern.metadata.title || 'Untitled Pattern'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {pattern.metadata.description || pattern.document.slice(0, 150) + '...'}
        </Typography>

        {/* Technologies */}
        <Box sx={{ mb: 2 }}>
          {pattern.metadata.technologies?.slice(0, 3).map((tech) => (
            <Chip
              key={tech}
              label={tech}
              size="small"
              sx={{ mr: 0.5, mb: 0.5 }}
              color="primary"
              variant="outlined"
            />
          ))}
          {pattern.metadata.technologies && pattern.metadata.technologies.length > 3 && (
            <Chip
              label={`+${pattern.metadata.technologies.length - 3} more`}
              size="small"
              sx={{ mr: 0.5, mb: 0.5 }}
              variant="outlined"
            />
          )}
        </Box>

        {/* Pattern type and similarity */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Chip
            label={pattern.metadata.pattern_type || 'unknown'}
            size="small"
            color="secondary"
          />
          {pattern.similarity_score !== undefined && (
            <Typography variant="caption" color="text.secondary">
              {Math.round(pattern.similarity_score * 100)}% match
            </Typography>
          )}
        </Box>
      </CardContent>

      <CardActions>
        <Button
          size="small"
          startIcon={<VisibilityIcon />}
          onClick={() => handlePatternDetail(pattern)}
        >
          View Details
        </Button>
        <Button size="small" startIcon={<ShareIcon />}>
          Share
        </Button>
        {pattern.metadata.validated && (
          <ThumbUpIcon color="success" fontSize="small" />
        )}
      </CardActions>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Pattern Search & Browse
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Search through our knowledge base of development patterns and solutions.
      </Typography>

      {/* Search Bar */}
      <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search patterns, technologies, or descriptions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
            }}
          />
          <Button
            variant="outlined"
            startIcon={<FilterListIcon />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
            {showFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </Button>
        </Box>

        {/* Advanced Filters */}
        <Collapse in={showFilters}>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Autocomplete
                multiple
                options={COMMON_TECHNOLOGIES}
                value={filters.technologies || []}
                onChange={(_, value) => handleFilterChange('technologies', value)}
                renderInput={(params) => (
                  <TextField {...params} label="Technologies" />
                )}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Project Type</InputLabel>
                <Select
                  value={filters.project_type || ''}
                  onChange={(e) => handleFilterChange('project_type', e.target.value)}
                  label="Project Type"
                >
                  <MenuItem value="">All Types</MenuItem>
                  {PROJECT_TYPES.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.replace('_', ' ')}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Complexity</InputLabel>
                <Select
                  value={filters.complexity || ''}
                  onChange={(e) => handleFilterChange('complexity', e.target.value)}
                  label="Complexity"
                >
                  <MenuItem value="">All Levels</MenuItem>
                  {COMPLEXITY_LEVELS.map((level) => (
                    <MenuItem key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography gutterBottom>Similarity Threshold</Typography>
              <Slider
                value={minSimilarity}
                onChange={(_, value) => setMinSimilarity(value as number)}
                min={0.5}
                max={1.0}
                step={0.05}
                marks={[
                  { value: 0.5, label: '50%' },
                  { value: 0.75, label: '75%' },
                  { value: 1.0, label: '100%' },
                ]}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${Math.round(value * 100)}%`}
              />
            </Grid>
          </Grid>
        </Collapse>
      </Paper>

      {/* Search Results */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {!loading && query.trim() && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Found {totalCount} patterns in {queryTime}ms
          </Typography>
        </Box>
      )}

      {!loading && patterns.length > 0 && (
        <>
          <Grid container spacing={3}>
            {patterns.map((pattern) => (
              <Grid item xs={12} sm={6} md={4} key={pattern.id}>
                <PatternCard pattern={pattern} />
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {totalCount > limit && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={Math.ceil(totalCount / limit)}
                page={page}
                onChange={(_, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      {!loading && query.trim() && patterns.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No patterns found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search terms or filters
          </Typography>
        </Box>
      )}

      {/* Pattern Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedPattern && (
          <>
            <DialogTitle>
              {selectedPattern.metadata.title || 'Pattern Details'}
              <Typography variant="body2" color="text.secondary">
                ID: {selectedPattern.id}
              </Typography>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={tabValue} onChange={(_, value) => setTabValue(value)}>
                  <Tab label="Description" icon={<DescriptionIcon />} />
                  <Tab label="Code" icon={<CodeIcon />} />
                </Tabs>
              </Box>

              <TabPanel value={tabValue} index={0}>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {selectedPattern.metadata.description || selectedPattern.document}
                </Typography>

                <Divider sx={{ my: 2 }} />

                <Typography variant="h6" gutterBottom>
                  Technologies
                </Typography>
                <Box sx={{ mb: 2 }}>
                  {selectedPattern.metadata.technologies?.map((tech) => (
                    <Chip
                      key={tech}
                      label={tech}
                      sx={{ mr: 0.5, mb: 0.5 }}
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>

                <Typography variant="h6" gutterBottom>
                  Pattern Type
                </Typography>
                <Chip
                  label={selectedPattern.metadata.pattern_type || 'unknown'}
                  color="secondary"
                  sx={{ mb: 2 }}
                />

                {selectedPattern.similarity_score !== undefined && (
                  <>
                    <Typography variant="h6" gutterBottom>
                      Similarity Score
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {Math.round(selectedPattern.similarity_score * 100)}% match
                    </Typography>
                  </>
                )}
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                    {selectedPattern.metadata.code || 'No code example available'}
                  </pre>
                </Paper>
              </TabPanel>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
              <Button variant="contained" startIcon={<ShareIcon />}>
                Share Pattern
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
}
