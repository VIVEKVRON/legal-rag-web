class HybridFusionService:
    @staticmethod
    def reciprocal_rank_fusion(dense_results, sparse_results, limit=20, rrf_k=60):
        if not dense_results and not sparse_results:
            return []
        if not dense_results:
            return sparse_results[:limit]
        if not sparse_results:
            return dense_results[:limit]
            
        rrf_scores = {}
        merged_results = {}
        
        for rank, res in enumerate(dense_results):
            point_id = res.id
            rrf_scores[point_id] = rrf_scores.get(point_id, 0.0) + (1.0 / (rrf_k + rank + 1))
            merged_results[point_id] = res

        for rank, res in enumerate(sparse_results):
            point_id = res.id
            rrf_scores[point_id] = rrf_scores.get(point_id, 0.0) + (1.0 / (rrf_k + rank + 1))
            merged_results[point_id] = res

        sorted_rrf_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:limit]
        return [merged_results[pid] for pid in sorted_rrf_ids]
